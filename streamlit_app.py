import streamlit as st
import pandas as pd
import tempfile
import os
import time
from pathlib import Path
import zipfile
from book_scraper import BookScraper
import base64

# Configure page
st.set_page_config(
    page_title="📚 Book Scraper & PDF Generator",
    page_icon="📚",
    layout="wide"
)

# Initialize session state
if 'chapters' not in st.session_state:
    st.session_state.chapters = []
if 'scraper' not in st.session_state:
    st.session_state.scraper = BookScraper()
if 'chapters_content' not in st.session_state:
    st.session_state.chapters_content = {}
if 'pdf_ready' not in st.session_state:
    st.session_state.pdf_ready = False
if 'pdf_path' not in st.session_state:
    st.session_state.pdf_path = None

def get_download_link(file_path, file_name):
    """Generate download link for file"""
    with open(file_path, "rb") as f:
        bytes_data = f.read()
    b64 = base64.b64encode(bytes_data).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{file_name}">📥 Download PDF</a>'
    return href

def extract_chapters(url):
    """Extract chapters from URL"""
    with st.spinner("🔍 Finding chapters..."):
        chapters = st.session_state.scraper.get_chapters(url)
        if chapters:
            # Create a dataframe for better display
            chapter_data = []
            for i, chapter_url in enumerate(chapters, 1):
                # Try to extract chapter title from URL
                title = chapter_url.split('/')[-1].replace('-', ' ').title()
                if not title or len(title) < 3:
                    title = f"Chapter {i}"
                chapter_data.append({
                    'order': i,
                    'title': title,
                    'url': chapter_url,
                    'include': True
                })
            return pd.DataFrame(chapter_data)
    return None

def download_chapters(chapter_df):
    """Download selected chapters"""
    selected_chapters = chapter_df[chapter_df['include']].copy()
    selected_chapters = selected_chapters.sort_values('order').reset_index(drop=True)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    chapters_content = {}
    
    for idx, row in selected_chapters.iterrows():
        progress = (idx + 1) / len(selected_chapters)
        progress_bar.progress(progress)
        status_text.text(f"📖 Downloading: {row['title']} ({idx + 1}/{len(selected_chapters)})")
        
        content = st.session_state.scraper.get_chapter_text(row['url'])
        if content:
            chapters_content[row['order']] = {
                'title': row['title'],
                'content': content,
                'url': row['url']
            }
        
        # Small delay to be respectful
        time.sleep(0.5)
    
    progress_bar.progress(1.0)
    status_text.text("✅ All chapters downloaded!")
    
    return chapters_content

def create_pdf(chapters_content, book_title="My Book"):
    """Create PDF from chapters content"""
    with st.spinner("📄 Generating PDF..."):
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        chapters_dir = Path(temp_dir) / "chapters"
        chapters_dir.mkdir(exist_ok=True)
        
        # Write chapters to markdown files
        for order, chapter_data in sorted(chapters_content.items()):
            chapter_file = chapters_dir / f"chapter-{order:03d}.md"
            with open(chapter_file, 'w', encoding='utf-8') as f:
                f.write(f"# {chapter_data['title']}\n\n")
                f.write(chapter_data['content'])
        
        # Generate PDF
        pdf_path = Path(temp_dir) / f"{book_title.replace(' ', '_')}.pdf"
        try:
            st.session_state.scraper.combine_to_pdf(str(chapters_dir), str(pdf_path))
            return str(pdf_path)
        except Exception as e:
            st.error(f"Error creating PDF: {e}")
            return None

# Main app
st.title("📚 Book Scraper & PDF Generator")
st.markdown("Transform web-based books into beautiful PDFs with full control over chapters!")

# Step 1: URL Input
st.header("1️⃣ Enter Book URL")
url = st.text_input(
    "Book URL:", 
    placeholder="https://example.com/book-page",
    help="Enter the main page URL of the book containing chapter links"
)

if url and st.button("🔍 Find Chapters", type="primary"):
    chapters_df = extract_chapters(url)
    if chapters_df is not None and not chapters_df.empty:
        st.session_state.chapters = chapters_df
        st.success(f"Found {len(chapters_df)} chapters!")
        st.rerun()
    else:
        st.error("No chapters found! Please check the URL or try a different book.")

# Step 2: Chapter Management
if len(st.session_state.chapters) > 0:
    st.header("2️⃣ Manage Chapters")
    st.markdown("**Rearrange and delete chapters as needed**")
    
    # Sort chapters by order
    sorted_chapters = st.session_state.chapters.sort_values('order').reset_index(drop=True)
    
    # Display each chapter with controls
    st.markdown("### 📚 Chapter List")
    
    for idx in range(len(sorted_chapters)):
        row = sorted_chapters.iloc[idx]
        
        # Create columns: [Move Up/Down] [Chapter Info] [Delete]
        col1, col2, col3 = st.columns([1, 8, 1])
        
        with col1:
            # Move up/down buttons in a compact layout
            subcol1, subcol2 = st.columns(2)
            with subcol1:
                if idx > 0:
                    if st.button("⬆️", key=f"up_{row['order']}", help="Move up"):
                        # Swap with previous chapter
                        prev_row = sorted_chapters.iloc[idx-1]
                        st.session_state.chapters.loc[st.session_state.chapters['order'] == row['order'], 'order'] = -1  # temp
                        st.session_state.chapters.loc[st.session_state.chapters['order'] == prev_row['order'], 'order'] = row['order']
                        st.session_state.chapters.loc[st.session_state.chapters['order'] == -1, 'order'] = prev_row['order']
                        st.rerun()
            with subcol2:
                if idx < len(sorted_chapters) - 1:
                    if st.button("⬇️", key=f"down_{row['order']}", help="Move down"):
                        # Swap with next chapter
                        next_row = sorted_chapters.iloc[idx+1]
                        st.session_state.chapters.loc[st.session_state.chapters['order'] == row['order'], 'order'] = -1  # temp
                        st.session_state.chapters.loc[st.session_state.chapters['order'] == next_row['order'], 'order'] = row['order']
                        st.session_state.chapters.loc[st.session_state.chapters['order'] == -1, 'order'] = next_row['order']
                        st.rerun()
        
        with col2:
            # Display chapter info in compact format
            container_style = """
            <div style="
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 8px 12px;
                margin: 2px 0;
                box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                min-height: 40px;
                display: flex;
                align-items: center;
            ">
                <div style="flex-grow: 1;">
                    <div style="font-weight: 500; font-size: 14px; margin-bottom: 2px; line-height: 1.2;">
                        {title}
                    </div>
                    <a href="{url}" target="_blank" style="
                        font-size: 11px; 
                        color: #0066cc; 
                        text-decoration: none;
                        word-break: break-all;
                        line-height: 1.1;
                    ">{url}</a>
                </div>
            </div>
            """.format(title=row['title'], url=row['url'])
            
            st.markdown(container_style, unsafe_allow_html=True)
        
        with col3:
            # Delete button with red X
            delete_button_style = """
            <style>
            .delete-button {
                background-color: #ff4444 !important;
                color: white !important;
                border: none !important;
                border-radius: 4px !important;
                padding: 4px 8px !important;
                font-size: 14px !important;
                font-weight: bold !important;
                cursor: pointer !important;
                min-height: 32px !important;
            }
            .delete-button:hover {
                background-color: #cc0000 !important;
            }
            </style>
            """
            st.markdown(delete_button_style, unsafe_allow_html=True)
            
            if st.button("✕", key=f"delete_{row['order']}", help="Delete chapter"):
                # Remove this chapter
                st.session_state.chapters = st.session_state.chapters[
                    st.session_state.chapters['order'] != row['order']
                ].reset_index(drop=True)
                
                # Reorder remaining chapters
                remaining_chapters = st.session_state.chapters.sort_values('order')
                for new_idx, (_, chapter_row) in enumerate(remaining_chapters.iterrows(), 1):
                    st.session_state.chapters.loc[
                        st.session_state.chapters['order'] == chapter_row['order'], 
                        'order'
                    ] = new_idx
                
                st.rerun()
    
    # Show chapter summary and book title input
    total_count = len(st.session_state.chapters)
    
    if total_count > 0:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"📊 {total_count} chapters ready for PDF generation")
        with col2:
            book_title = st.text_input("Book Title:", value="My Book", key="book_title")
    
    # Step 3: Generate PDF
    if total_count > 0:
        st.header("3️⃣ Generate PDF")
        
        if st.button("🚀 Download Chapters & Create PDF", type="primary"):
            # Download chapters (only the ones remaining in the list)
            st.session_state.chapters_content = download_chapters(st.session_state.chapters)
            
            if st.session_state.chapters_content:
                # Create PDF
                pdf_path = create_pdf(st.session_state.chapters_content, book_title)
                
                if pdf_path:
                    st.session_state.pdf_path = pdf_path
                    st.session_state.pdf_ready = True
                    st.rerun()

# Step 4: Download PDF
if st.session_state.pdf_ready and st.session_state.pdf_path:
    st.header("4️⃣ Download Your Book")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.success("🎉 Your PDF is ready!")
        
        # Provide download button
        with open(st.session_state.pdf_path, "rb") as pdf_file:
            pdf_bytes = pdf_file.read()
            
        st.download_button(
            label="📥 Download PDF",
            data=pdf_bytes,
            file_name=f"{st.session_state.get('book_title', 'My_Book')}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )
    
    with col2:
        # Show file info
        file_size = len(pdf_bytes) / (1024 * 1024)  # MB
        chapter_count = len(st.session_state.chapters_content)
        st.metric("File Size", f"{file_size:.1f} MB")
        st.metric("Chapters", chapter_count)

# Sidebar info
with st.sidebar:
    st.header("ℹ️ How to Use")
    st.markdown("""
    1. **Enter URL** - Paste the main book page URL
    2. **Manage Chapters** - Select, reorder, and rename chapters
    3. **Generate PDF** - Download chapters and create PDF
    4. **Download** - Get your formatted book!
    
    ### 📝 Tips:
    - Use the checkboxes to exclude unwanted chapters
    - Drag rows to reorder chapters
    - Edit titles for better formatting
    - Be patient - large books take time!
    
    ### ⚠️ Legal Note:
    Only scrape content you have permission to access. Respect website terms of service and copyright laws.
    """)
    
    # Reset button
    if st.button("🔄 Start Over"):
        for key in ['chapters', 'chapters_content', 'pdf_ready', 'pdf_path']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit | Respect website terms of service") 