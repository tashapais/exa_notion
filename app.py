import streamlit as st
import os
from dotenv import load_dotenv
from exa_py import Exa
from notion_client import Client

# Load environment variables
load_dotenv()

# Initialize Exa client
exa = Exa(api_key=os.environ['EXA_API_KEY'])

# Initialize Notion client
notion = Client(auth=os.environ['NOTION_API_KEY'])

def get_notion_page_content(page_id):
    blocks = []
    next_cursor = None
    while True:
        response = notion.blocks.children.list(block_id=page_id, start_cursor=next_cursor, page_size=100)
        blocks.extend(response['results'])
        if not response.get('has_more'):
            break
        next_cursor = response['next_cursor']

    content = ""
    for block in blocks:
        block_type = block['type']
        if block_type in ['paragraph', 'heading_1', 'heading_2', 'heading_3', 'bulleted_list_item', 'numbered_list_item']:
            rich_text = block[block_type]['rich_text']
            if rich_text:
                if block_type == 'heading_1':
                    content += "# "
                elif block_type == 'heading_2':
                    content += "## "
                elif block_type == 'heading_3':
                    content += "### "
                elif block_type in ['bulleted_list_item', 'numbered_list_item']:
                    content += "- "
                content += rich_text[0]['plain_text'] + "\n\n"
        # Add more block types as needed

    return content

def search_interests(query, category=None):
    response = exa.search_and_contents(
        query,
        use_autoprompt=True,
        num_results=5,
        category=category,
        text={"max_characters": 1000},
        highlights=True
    )
    
    results = []
    for result in response.results:
        results.append({
            "title": result.title,
            "url": result.url,
            "highlight": result.highlights[0] if result.highlights else 'N/A'
        })
    return results

# Streamlit UI
st.title("Notion-Prompted Interest Search")

# Sidebar for Notion page ID input
notion_page_id = st.sidebar.text_input("Enter your Notion page ID")

if notion_page_id:
    notion_content = get_notion_page_content(notion_page_id)
    
    # Main content area with two columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Notion Page Content")
        st.markdown(notion_content)  # Use markdown instead of write
    
    with col2:
        st.subheader("Search Results")
        query = st.text_input("Enter your search query")
        category = st.selectbox("Select a category (optional)", [None, "github", "videos"])
        
        if st.button("Search"):
            if query:
                results = search_interests(query, category)
                for result in results:
                    st.markdown(f"**{result['title']}**")
                    st.write(f"URL: {result['url']}")
                    st.write(f"Highlight: {result['highlight']}")
                    st.markdown("---")
            else:
                st.warning("Please enter a search query")
else:
    st.warning("Please enter a Notion page ID in the sidebar")