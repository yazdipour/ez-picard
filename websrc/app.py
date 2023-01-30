# cheatsheet https://daniellewisdl-streamlit-cheat-sheet-app-ytm9sg.streamlit.app
import os
from streamlit_extras.word_importances import format_word_importances
import streamlit as st
from streamlit_extras.badges import badge
from streamlit_extras.customize_running import center_running
from streamlit_extras.mention import mention
import numpy as np
import client
import pandas as pd

# @st.cache(allow_output_mutation=True)


def setup_pipeline(model: str, device: int = 0):
    global model_name
    model_name = model


# ------------------ Constants ------------------
# These "LM adapted" models are initialized from t5.1.1 (above) and train for an additional 100K steps on the LM objective discussed in the T5 paper. This adaptation improves the ability of the model to be used for prompt tuning.
# https: // github.com/google-research/text-to-text-transfer-transformer/blob/main/released_checkpoints.md
models_list = {
    "spider.t5.lm100k.base": "tscholak/1zha5ono",
    "spider.t5.lm100k.large.71.2": "tscholak/3vnuv1vf",
    "spider.T5.Large.65.3": "tscholak/1wnr382e",
    "cosql.t5.lm100k.large": "tscholak/2jrayxos"
}
db_types_list = ["mysql", "sqlserver", "postgres"]
# ------------------ Streamlit ------------------

project_name = "EZ-PICARD Text2SQL"
st.set_page_config(
    page_title=project_name,
    page_icon="🤖",
)
# streamlit set light theme
st.markdown(
    """
    <style>
    .reportview-container {
        background: #f5f5f5
    }
    .sidebar .sidebar-content {
        background: #f5f5f5
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title(f"🤖 {project_name}")

# Sidebar
with st.sidebar:
    with open(os.path.join(
            os.path.dirname(__file__), 'README.md'), 'r') as f:
        st.markdown(f.read())
    with st.expander("About", True):
        st.write(
            'This web application simplifies the setup and usage of text-to-sql picard by providing an easy-to-use interface for integrating and querying databases using natural language.')
        mention(
            label="yazdipour/ez-picard",
            icon="github",
            url="https://github.com/yazdipour/ez-picard/"
        )
    with st.expander("🧊 Models", True):
        if model_radio := st.radio(
            "Choose Text2SQL model to use:",
            models_list.keys(),
            index=0,
            key="model_type",
        ):
            translator = setup_pipeline(models_list[model_radio])

    with st.expander("🧩 Examples", True):
        if st.button("What are the names?"):
            st.session_state['text_question'] = 'Give me field and username of changelogs of fixed issues in version "0.13"'
            st.session_state['text_db_id'] = "apache-pig"
            st.session_state[
                'text_schema'] = 'jira_repository : key , base_url | git_repository : git_repository_id , name , url , checkout_hash | meta : key , value | issue : issue_id , type , created_date , created_date_zoned , updated_date , updated_date_zoned , resolved_date , resolved_date_zoned , summary , description , priority , status , resolution , assignee , assignee_username , reporter , reporter_username | code_change : commit_hash foreign key change_set  , file_path , old_file_path , change_type , patch_type , is_deleted , sum_added_lines , sum_removed_lines | issue_attachment : issue_id foreign key issue  , username , display_name , created_date , created_date_zoned , mime_type , content , filename , size_bytes | issue_changelog : issue_id foreign key issue  , username , display_name , created_date , created_date_zoned , group_id , field_type , field ( Version ) , from_value , from_string ( 0.12.1 , patch ) , to_value , to_string ( 0.12.1 , patch ) | issue_comment : issue_id foreign key issue  , username , display_name , created_date , created_date_zoned , message ( Patch , patch ) | issue_component : issue_id foreign key issue  , component | issue_fix_version : issue_id foreign key issue  , fix_version ( 0.12.1 ) | issue_link : source_issue_id foreign key issue  , target_issue_id foreign key issue  , name , outward_label , is_containment | change_set : commit_hash , git_repository_id , committed_date , committed_date_zoned , message , author , author_email , is_merge | change_set_link : commit_hash foreign key change_set'
# ------------ MAIN PAGE ------------

# Shows Available DBs
with st.expander("🏬 Available DBs", True):
    # if clicked on button, get list of dbs
    if st.button("🔍 List DBs"):
        dbs_list = client.get_list_dbs()
        st.write(dbs_list)

# Upload DB Form
with st.expander("🆙 Upload SQLite DB", True):
    # upload sqlite db file using streamlit file uploader
    uploaded_file = st.file_uploader("Choose a file", type=["sqlite"])
    if uploaded_file is not None:
        file_details = {"FileName": uploaded_file.name,
                        "FileType": uploaded_file.type,
                        "FileSize": uploaded_file.size}
        st.write(file_details)
        # save file to disk
        path = f'/database/{uploaded_file.name.split(".")[0]}'
        os.makedirs(path, exist_ok=True)
        with open(f'{path}/{uploaded_file.name}', "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success("File successfully saved.")

# Text2SQL Form
with st.form(key="my_form"):
    st.text_input(
        "DB name:",
        key="text_db_id",
    )
    st.text_input(
        "Your question:",
        key="text_question",
        max_chars=100
    )
    st.text_area(
        "Enter your schema:",
        key="text_schema",
        help="SELECT JSON_ARRAYAGG( JSON_OBJECT( 'table', table_name, 'name', column_name ) ) FROM information_schema.columns WHERE table_name LIKE '%' and table_schema = 'DATABASE_NAME'",
    )
    if submit_button := st.form_submit_button("✨ Generate SQL ✨"):
        try:
            center_running()
            text_schema = st.session_state['text_schema']
            output = client.get_translate(
                st.session_state['text_question'],
                st.session_state['text_db_id'])
            st.code(output[0]['query'], language='sql')
            if execution_results := output[0]['execution_results']:
                # convert execution_results to pandas dataframe
                df = pd.DataFrame(execution_results)
                # display dataframe
                st.dataframe(df)

        except Exception as e:
            st.error(f"🚧 Error:{e} 🚧")

# Proxy DB Form
with st.expander("⚾ Proxy DB", False):
    with st.form(key="mysql_form"):
        model_radio = st.radio("Choose Database type to use:",
                               db_types_list, index=0, disabled=True, key="db_type")
        st.text_input(
            "Enter Host:",
            key="text_host",
            value="localhost"
        )
        st.text_input(
            "Enter Port:",
            key="text_port",
            value="3306"
        )
        st.text_input(
            "Enter Username:",
            key="text_username",
            value="root"
        )
        st.text_input(
            "Enter password:",
            key="text_password",
            value="root"
        )
        st.text_input(
            "Enter your DB name:",
            key="text_db_name",
            value="chinook"
        )
        if st.form_submit_button("✨ Proxy SQL ✨"):
            st.write("Proxying your DB...")
            config = {
                "host": st.session_state['text_host'],
                "port": st.session_state['text_port'],
                "user": st.session_state['text_username'],
                "password": st.session_state['text_password'],
                "database": st.session_state['text_db_name'],
            }
            st.info(client.proxy_mysql(config))
