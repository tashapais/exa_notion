import streamlit as st
import os
from dotenv import load_dotenv
from exa_py import Exa
from notion_client import Client
import networkx as nx
from pyvis.network import Network
import tempfile

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

def create_network_graph(results):
    G = nx.Graph()
    
    # Add nodes for each result
    for i, result in enumerate(results):
        G.add_node(i, title=result['title'], url=result['url'])
    
    # Add edges based on some similarity metric
    # This is a simple example; you may want to use a more sophisticated similarity measure
    for i in range(len(results)):
        for j in range(i+1, len(results)):
            # Simple similarity: check if titles share any words
            words_i = set(results[i]['title'].lower().split())
            words_j = set(results[j]['title'].lower().split())
            if words_i.intersection(words_j):
                G.add_edge(i, j)
    
    # Create a Pyvis network from our NetworkX graph
    net = Network(notebook=True, width="100%", height="500px", bgcolor="#222222", font_color="white")
    net.from_nx(G)
    
    # Generate the HTML file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmpfile:
        net.save_graph(tmpfile.name)
        return tmpfile.name

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
        category = st.selectbox("Select a category (optional)", [None, "github", "videos", "substack"])
        
        if st.button("Search"):
            if query:
                results = search_interests(query, category)
                
                # Display results
                for result in results:
                    st.markdown(f"**{result['title']}**")
                    st.write(f"URL: {result['url']}")
                    st.write(f"Highlight: {result['highlight']}")
                    st.markdown("---")
                
                # Create and display network graph
                if len(results) > 1:  # We need at least 2 results to create a graph
                    st.subheader("Results Network Graph")
                    graph_html = create_network_graph(results)
                    st.components.v1.html(open(graph_html, 'r').read(), height=600)
                    os.unlink(graph_html)  # Delete the temporary file
            else:
                st.warning("Please enter a search query")
else:
    st.warning("Please enter a Notion page ID in the sidebar")
