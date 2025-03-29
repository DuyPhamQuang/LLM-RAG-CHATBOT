import streamlit as st
from api_utils import upload_document, list_documents, delete_document

def display_sidebar():
    """
    Displays the sidebar that allows users to choose models, upload documents and list / delete existing documents.
    """
    # Model selection
    model_options = ["gemma3:4b", "gemma3:1b"]
    st.sidebar.selectbox("Select Model", options=model_options, key="model") #the user’s selection is automatically stored in st.session_state under the key

    # Document upload
    uploaded_file = st.sidebar.file_uploader("Choose a file", type=["pdf", "docx", "html"])
    if uploaded_file is not None and st.sidebar.button("Upload"):
        with st.spinner("Uploading..."):
            """
            Uploads the selected file to the server. If the upload is successful,
            the file ID is displayed in the sidebar.
            """
            upload_response = upload_document(uploaded_file)
            if upload_response is not None:
                st.sidebar.success(f"File uploaded successfully with ID {upload_response['file_id']}.")
                st.session_state.documents = list_documents()

    # List and delete documents
    st.sidebar.header("Uploaded Documents")
    if st.sidebar.button("Refresh Document List"):
        """
        Refreshes the document list by querying the server for the latest document list.
        """
        st.session_state.documents = list_documents()
    # Display document list and delete functionality
    if "documents" in st.session_state and st.session_state.documents is not None:
        for doc in st.session_state.documents:
            st.sidebar.text(f"{doc['filename']} (ID: {doc['id']})")
        """
        Displays the list of uploaded documents in the sidebar. Each document is
        displayed as a text element with the filename and ID.
        """

        selected_file_id = st.sidebar.selectbox("Select a document to delete", 
                                                options=[doc['id'] for doc in st.session_state.documents])
        if st.sidebar.button("Delete Selected Document"):
            """
            Deletes the selected document from the server. If the deletion is successful,
            a success message is displayed in the sidebar.
            """
            delete_response = delete_document(selected_file_id)
            if delete_response is not None:
                st.sidebar.success(f"Document deleted successfully.")
                st.session_state.documents = list_documents()
