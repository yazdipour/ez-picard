from fastapi.openapi.utils import get_openapi
import shutil
from typing import Optional
from seq2seq.utils.dataset import DataTrainingArguments
from seq2seq.utils.picard_model_wrapper import PicardArguments, PicardLauncher, with_picard
from seq2seq.utils.pipeline import Text2SQLGenerationPipeline, Text2SQLInput
from sqlite3 import Connection, connect, OperationalError
from uvicorn import run
from fastapi import FastAPI, HTTPException, Body, File, UploadFile
from transformers.models.auto import AutoConfig, AutoTokenizer, AutoModelForSeq2SeqLM
from transformers.hf_argparser import HfArgumentParser
from contextlib import nullcontext
import os
from pydantic import BaseModel
from dataclasses import dataclass, field
import sys
import logging

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s -   %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
    level=logging.WARNING,
)
logger = logging.getLogger(__name__)


@dataclass
class BackendArguments:
    """
    Arguments pertaining to model serving.
    """

    model_path: str = field(
        default="tscholak/1zha5ono",
        metadata={"help": "Path to pretrained model"},
    )
    cache_dir: Optional[str] = field(
        default="/tmp",
        metadata={"help": "Where to cache pretrained models and data"},
    )
    db_path: str = field(
        default="/database",
        metadata={"help": "Where to to find the sqlite files"},
    )
    host: str = field(default="0.0.0.0", metadata={
                      "help": "Bind socket to this host"})
    port: int = field(default=8000, metadata={
                      "help": "Bind socket to this port"})
    device: int = field(
        default=-1,
        metadata={
            "help": "Device ordinal for CPU/GPU supports. Setting this to -1 will leverage CPU. A non-negative value will run the model on the corresponding CUDA device id."
        },
    )


def delete_folders(path, dir_to_keep):
    # get a list of all the subdirectories in the specified path
    subdirectories = [d for d in os.listdir(
        path) if os.path.isdir(os.path.join(path, d))]
    for subdir in subdirectories:
        if subdir == dir_to_keep:
            continue
        subdir_path = os.path.join(path, subdir)
        shutil.rmtree(subdir_path)


def main():
    # See all possible arguments by passing the --help flag to this program.
    parser = HfArgumentParser(
        (PicardArguments, BackendArguments, DataTrainingArguments))
    picard_args: PicardArguments
    backend_args: BackendArguments
    data_training_args: DataTrainingArguments
    if len(sys.argv) == 2 and sys.argv[1].endswith(".json"):
        # If we pass only one argument to the script and it's the path to a json file,
        # let's parse it to get our arguments.
        picard_args, backend_args, data_training_args = parser.parse_json_file(
            json_file=os.path.abspath(sys.argv[1]))
    else:
        picard_args, backend_args, data_training_args = parser.parse_args_into_dataclasses()

    # Initialize config
    config = AutoConfig.from_pretrained(
        backend_args.model_path,
        cache_dir=backend_args.cache_dir,
        max_length=data_training_args.max_target_length,
        num_beams=data_training_args.num_beams,
        num_beam_groups=data_training_args.num_beam_groups,
        diversity_penalty=data_training_args.diversity_penalty,
    )

    # Initialize tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        backend_args.model_path,
        cache_dir=backend_args.cache_dir,
        use_fast=True,
    )

    # Initialize Picard if necessary
    with PicardLauncher() if picard_args.launch_picard else nullcontext(None):
        # Get Picard model class wrapper
        if picard_args.use_picard:
            def model_cls_wrapper(model_cls): return with_picard(
                model_cls=model_cls, picard_args=picard_args, tokenizer=tokenizer
            )
        else:
            def model_cls_wrapper(model_cls): return model_cls

        # Initialize model
        model = model_cls_wrapper(AutoModelForSeq2SeqLM).from_pretrained(
            backend_args.model_path,
            config=config,
            cache_dir=backend_args.cache_dir,
        )

        # Initalize generation pipeline
        pipe = Text2SQLGenerationPipeline(
            model=model,
            tokenizer=tokenizer,
            db_path=backend_args.db_path,
            prefix=data_training_args.source_prefix,
            normalize_query=data_training_args.normalize_query,
            schema_serialization_type=data_training_args.schema_serialization_type,
            schema_serialization_with_db_id=data_training_args.schema_serialization_with_db_id,
            schema_serialization_with_db_content=data_training_args.schema_serialization_with_db_content,
            device=backend_args.device,
        )

        # Initialize REST API
        app = FastAPI()

        def custom_openapi():
            if app.openapi_schema:
                return app.openapi_schema
            openapi_schema = get_openapi(
                title="EZ-PICARD",
                version="0.0.1",
                description="EZ-PICARD is a eazy implementation of the PICARD framework for text-to-SQL generation.",
                routes=app.routes,
            )
            app.openapi_schema = openapi_schema
            return app.openapi_schema

        app.openapi = custom_openapi

        class AskResponse(BaseModel):
            query: str
            execution_results: list

        def response(query: str, conn: Connection) -> AskResponse:
            try:
                return AskResponse(query=query, execution_results=conn.execute(query).fetchall())
            except OperationalError as e:
                raise HTTPException(
                    status_code=500, detail=f'while executing "{query}", the following error occurred: {e.args[0]}'
                )

        @app.get("/ask/{db_id}/{question}")
        def ask(db_id: str = 'chinook', question: str = 'how many singers we have?'):
            try:
                outputs = pipe(
                    inputs=Text2SQLInput(utterance=question, db_id=db_id),
                    num_return_sequences=data_training_args.num_return_sequences,
                )
            except OperationalError as e:
                raise HTTPException(status_code=404, detail=e.args[0])
            try:
                conn = connect(
                    f"{backend_args.db_path}/{db_id}/{db_id}.sqlite")
                return [response(query=output["generated_text"], conn=conn) for output in outputs]
            finally:
                conn.close()

        @app.get("/dbs")
        def dbs():
            return [db for db in os.listdir(backend_args.db_path) if os.path.isdir(os.path.join(backend_args.db_path, db))]

        @app.post("/upload/")
        async def upload(file: UploadFile = File(...)):
            try:
                # delete_folders(backend_args.db_path, "chinook")
                path = f'{backend_args.db_path}/{file.filename.split(".")[0]}'
                os.makedirs(path, exist_ok=True)
                with open(f'{path}/{file.filename}', 'wb') as f:
                    shutil.copyfileobj(file.file, f)
            except Exception as e:
                raise HTTPException(status_code=400, detail=e)
            finally:
                file.file.close()
            return {"message": f"Successfully uploaded {file.filename}"}

        # # post request that gets configs, db_id and question and model_path
        @app.post("/ask/{db_id}/{question}")
        def ask(db_id: str = 'chinook', question: str = 'how many singers we have?', backend_args: dict = Body(...)):
            try:
                config = AutoConfig.from_pretrained(
                    backend_args['model_path'],
                    cache_dir=backend_args['cache_dir'],
                    max_length=data_training_args.max_target_length,
                    num_beams=data_training_args.num_beams,
                    num_beam_groups=data_training_args.num_beam_groups,
                    diversity_penalty=data_training_args.diversity_penalty,
                )
                model = model_cls_wrapper(AutoModelForSeq2SeqLM).from_pretrained(
                    backend_args["model_path"],
                    config=config,
                    cache_dir=backend_args['cache_dir'],
                )
                pipe = Text2SQLGenerationPipeline(
                    model=model,
                    tokenizer=tokenizer,
                    db_path=backend_args['db_path'],
                    prefix=data_training_args.source_prefix,
                    normalize_query=data_training_args.normalize_query,
                    schema_serialization_type=data_training_args.schema_serialization_type,
                    schema_serialization_with_db_id=data_training_args.schema_serialization_with_db_id,
                    schema_serialization_with_db_content=data_training_args.schema_serialization_with_db_content,
                    device=backend_args['device'],
                )
                outputs = pipe(
                    inputs=Text2SQLInput(utterance=question, db_id=db_id),
                    num_return_sequences=1,
                )
            except OperationalError as e:
                raise HTTPException(status_code=404, detail=e)
            try:
                conn = connect(
                    f"{backend_args.db_path}/{db_id}/{db_id}.sqlite")
                return [response(query=output["generated_text"], conn=conn) for output in outputs]
            finally:
                conn.close()

        # Run app
        run(app=app, host=backend_args.host, port=backend_args.port)


if __name__ == "__main__":
    main()
