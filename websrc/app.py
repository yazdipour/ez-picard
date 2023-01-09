# cheatsheet https://daniellewisdl-streamlit-cheat-sheet-app-ytm9sg.streamlit.app
import os
from streamlit_extras.word_importances import format_word_importances
import streamlit as st
from streamlit_extras.badges import badge
from streamlit_extras.customize_running import center_running
from streamlit_extras.mention import mention
import numpy as np
import client

# @st.cache(allow_output_mutation=True)


def setup_pipeline(model: str, device: int = 0):
    global model_name
    model_name = model


def translate_question(question: str, db_id: str):
    return f"{question} | {db_id}"


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

# translator = setup_pipeline("tscholak/1zha5ono")
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
        model_radio = st.radio("Choose Text2SQL model to use:",
                               models_list.keys(), index=0, key="model_type")
        if model_radio:
            translator = setup_pipeline(models_list[model_radio])

    with st.expander("🧩 Examples", True):
        if st.button("What are the names?"):
            st.session_state['text_question'] = "What are the name of the singers?"
            st.session_state['text_db_id'] = "concert_singer"
            st.session_state['text_schema'] = '[{"name": "addressLine1", "table": "customers"}, {"name": "addressLine2", "table": "customers"}, {"name": "city", "table": "customers"}, {"name": "contactFirstName", "table": "customers"}, {"name": "contactLastName", "table": "customers"}, {"name": "country", "table": "customers"}, {"name": "creditLimit", "table": "customers"}, {"name": "customerName", "table": "customers"}, {"name": "customerNumber", "table": "customers"}, {"name": "phone", "table": "customers"}, {"name": "postalCode", "table": "customers"}, {"name": "salesRepEmployeeNumber", "table": "customers"}, {"name": "state", "table": "customers"}, {"name": "email", "table": "employees"}, {"name": "employeeNumber", "table": "employees"}, {"name": "extension", "table": "employees"}, {"name": "firstName", "table": "employees"}, {"name": "jobTitle", "table": "employees"}, {"name": "lastName", "table": "employees"}, {"name": "officeCode", "table": "employees"}, {"name": "reportsTo", "table": "employees"}, {"name": "addressLine1", "table": "offices"}, {"name": "addressLine2", "table": "offices"}, {"name": "city", "table": "offices"}, {"name": "country", "table": "offices"}, {"name": "officeCode", "table": "offices"}, {"name": "phone", "table": "offices"}, {"name": "postalCode", "table": "offices"}, {"name": "state", "table": "offices"}, {"name": "territory", "table": "offices"}, {"name": "orderLineNumber", "table": "orderdetails"}, {"name": "orderNumber", "table": "orderdetails"}, {"name": "priceEach", "table": "orderdetails"}, {"name": "productCode", "table": "orderdetails"}, {"name": "quantityOrdered", "table": "orderdetails"}, {"name": "comments", "table": "orders"}, {"name": "customerNumber", "table": "orders"}, {"name": "orderDate", "table": "orders"}, {"name": "orderNumber", "table": "orders"}, {"name": "requiredDate", "table": "orders"}, {"name": "shippedDate", "table": "orders"}, {"name": "status", "table": "orders"}, {"name": "amount", "table": "payments"}, {"name": "checkNumber", "table": "payments"}, {"name": "customerNumber", "table": "payments"}, {"name": "paymentDate", "table": "payments"}, {"name": "htmlDescription", "table": "productlines"}, {"name": "image", "table": "productlines"}, {"name": "productLine", "table": "productlines"}, {"name": "textDescription", "table": "productlines"}, {"name": "buyPrice", "table": "products"}, {"name": "MSRP", "table": "products"}, {"name": "productCode", "table": "products"}, {"name": "productDescription", "table": "products"}, {"name": "productLine", "table": "products"}, {"name": "productName", "table": "products"}, {"name": "productScale", "table": "products"}, {"name": "productVendor", "table": "products"}, {"name": "quantityInStock", "table": "products"}]'
            st.session_state['text_pquestion'] = "How many singers do we have?"

# Main Body
# Text2SQL Form
with st.form(key="my_form"):
    st.text_input(
        "Enter your question:",
        key="text_question",
        max_chars=100
    )
    st.text_input(
        "Enter your DB name:",
        key="text_db_id",
    )
    # st.text_area(
    #     "Enter your schema:",
    #     key="text_schema",
    #     help="SELECT JSON_ARRAYAGG( JSON_OBJECT( 'table', table_name, 'name', column_name ) ) FROM information_schema.columns WHERE table_name LIKE '%' and table_schema = 'DATABASE_NAME'",
    # )
    submit_button = st.form_submit_button("✨ Generate SQL ✨")
    if submit_button:
        try:
            center_running()
            text_schema = st.session_state['text_schema']
            output = translate_question(
                translator, st.session_state['text_question'], st.session_state['text_db_id'])
            st.code(output, language='sql')
        except Exception as e:
            st.error("🚧 Error:{} 🚧".format(e))

# Upload DB Form
with st.expander("🆙 Upload SQLite DB", True):
    # upload sqlite db file using streamlit file uploader
    uploaded_file = st.file_uploader("Choose a file", type=["sqlite"])
    if uploaded_file is not None:
        file_details = {"FileName": uploaded_file.name,
                        "FileType": uploaded_file.type, "FileSize": uploaded_file.size}
        st.write(file_details)
        client.upload(uploaded_file.getvalue())
        st.success("File successfully saved.")


# Proxy DB Form
with st.expander("⚾ Proxy DB", True):
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


input_text = "How many singers do we have"
encoder_out = [[571,  186, 7634,    7,  103,   62,   43,    1]][0][1:-1]

output_text = "Wie viele Sänger haben wir?"
decoder_out = [[0,  2739,  2584, 3324,   1745,   558,    58,     1]][0][2:-1]
def normalize(x): return (x - np.min(x)) / (np.max(x) - np.min(x))


st.write(format_word_importances(
    words=input_text.split(),
    importances=encoder_out/np.max(encoder_out),
), unsafe_allow_html=True)
st.write(format_word_importances(
    words=output_text.split(),
    importances=normalize(decoder_out),
), unsafe_allow_html=True)
