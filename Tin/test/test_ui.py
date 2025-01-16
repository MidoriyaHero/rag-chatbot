import base64
import logging
import time
from collections.abc import Iterable
from enum import Enum
from pathlib import Path
from typing import Any

import gradio as gr  # type: ignore
from gradio.themes.utils.colors import slate  # type: ignore
from pydantic import BaseModel


logger = logging.getLogger(__name__)



class Modes(str, Enum):
    """Available modes for the Private GPT UI."""
    RAG_MODE = "RAG"
    SEARCH_MODE = "Search"
    BASIC_CHAT_MODE = "Basic"
    SUMMARIZE_MODE = "Summarize"


MODES: list[Modes] = [
    Modes.RAG_MODE,
    Modes.SEARCH_MODE,
    Modes.BASIC_CHAT_MODE,
    Modes.SUMMARIZE_MODE,
]


class Source(BaseModel):
    """Represents a curated source of text, used to display chunk references."""
    file: str
    page: str
    text: str

    class Config:
        frozen = True





class PrivateGptUi:
    def __init__(self):
        pass

        


    # --- File handling logic ---



    def _build_ui_blocks(self) -> gr.Blocks:
        """
        Construct the Gradio interface: Layout of columns/rows,
        chat interface, file upload, etc.
        """
        logger.debug("Creating the UI blocks")

        with gr.Blocks(
            title='Grad',
            theme=gr.themes.Soft(primary_hue=slate),
            css="""
.logo { 
  display: flex;
  width: 100%;            /* Ensure the parent spans full width */
  border-radius: 8px;
  align-items: center;    /* Center vertically */
  justify-content: center; /* Center horizontally */
}

.logo img { 
  max-height: 10vh;
  width: 100%;           /* Stretch logo image to fill parent width */
  height: auto;          /* Maintain aspect ratio */
  object-fit: cover;     /* Crops/zooms if aspect ratio doesn’t match parent */
}
.contain { 
  display: flex !important; 
  flex-direction: column !important; 
}

#component-0, #component-3, #component-10, #component-8 {
  height: 100% !important; 
}

#chatbot { 
  flex-grow: 1 !important; 
  overflow: auto !important;
}

#col { 
  height: calc(100vh - 112px - 16px) !important; 
}

hr { 
  margin-top: 1em; 
  margin-bottom: 1em; 
  border: 0; 
  border-top: 1px solid #FFF; 
}

.avatar-image { 
  background-color: antiquewhite; 
  border-radius: 2px; 
}

.footer { 
  text-align: center; 
  margin-top: 20px; 
  font-size: 14px; 
  display: flex; 
  align-items: center; 
  justify-content: center; 
}

.footer-zylon-link { 
  display: flex; 
  margin-left: 5px; 
  text-decoration: auto; 
  color: var(--body-text-color); 
}

.footer-zylon-link:hover { 
  color: #C7BAFF; 
}

.footer-zylon-ico { 
  height: 20px; 
  margin-left: 5px; 
  background-color: antiquewhite; 
  border-radius: 2px; 
}

#toggle {
  width: 10vh;
  border: 5px;

}
"""
        ) as blocks:
            # Header row with logo
            with gr.Row():
                gr.HTML(f"<div class='logo'><img src='https://digital.fpt.com/wp-content/themes/fdx/assets/images/branding-guideline/bg-top@3x.png'/></div>")
            def toggle_sidebar(state):
                state = not state
                return gr.update(visible = state), state

            # Main layout: Left column (modes, file mgmt) / Right column (chat)
            with gr.Row(equal_height=False):
                with gr.Column(visible=False) as sidebar_left:
                    gr.Markdown("SideBar Left")

                    mode = gr.Radio(
                        [m.value for m in MODES],
                        label="Mode",
                        
                        interactive=True,
                        show_label=True
                    )

                    # Explanation area
                    explanation_mode = gr.Textbox(
                        
                        show_label=False,
                        max_lines=3,
                        interactive=False,
                        
                    )

                    # Upload button
                    upload_button = gr.UploadButton(
                        label="Upload File(s)",
                        type="filepath",
                        file_count="multiple",
                        size="sm",
                    )

                    # List of ingested files
                    ingested_dataset = gr.List(
                    
                        headers=["File Name"],
                        label="Ingested Files",
                        height=225,
                        interactive=False,
                        render=False,
                    )

                    # Wire up the upload button
                    upload_button.upload(
                        
                        inputs=upload_button,
                        outputs=ingested_dataset,
                    )
                    ingested_dataset.change(
                        
                        outputs=ingested_dataset,
                    )
                    ingested_dataset.render()

                    # Deselect a file
                    deselect_file_button = gr.Button(
                        "De-select selected file",
                        size="sm",
                        interactive=False,
                    )

                    # Display which file is selected
                    selected_text = gr.Textbox(
                        "All files",
                        label="Selected for Query or Deletion",
                        max_lines=1,
                        interactive=False
                    )

                    # Delete one or all files
                    delete_file_button = gr.Button(
                        "🗑️ Delete selected file",
                        size="sm",
                        
                        interactive=False,
                    )
                    delete_files_button = gr.Button(
                        "⚠️ Delete ALL files",
                        size="sm",
                        
                    )

                    # Hook up events for file selection/deselection
                    deselect_file_button.click(
                        
                        outputs=[delete_file_button, deselect_file_button, selected_text],
                    )
                    ingested_dataset.select(
                        
                        outputs=[delete_file_button, deselect_file_button, selected_text],
                    )
                    delete_file_button.click(
                        
                        outputs=[ingested_dataset, delete_file_button, deselect_file_button, selected_text],
                    )
                    delete_files_button.click(
                        
                        outputs=[ingested_dataset, delete_file_button, deselect_file_button, selected_text],
                    )

                    # System prompt
                    system_prompt_input = gr.Textbox(
                       
                        label="System Prompt",
                        lines=2,
                        interactive=True,
                        
                    )

                    # On mode change -> reset system prompt and explanation
                    mode.change(
                        
                        inputs=mode,
                        outputs=[system_prompt_input, explanation_mode],
                    )
                    # On user blur -> update system prompt
                    system_prompt_input.blur(
                        
                        inputs=system_prompt_input,
                        outputs=None,
                    )

                # Right column for chat interface
                with gr.Column(scale=7, elem_id="col"):
                    sidebar_state = gr.State(False)

                    btn_toggle_sidebar = gr.Button("Sidebar", elem_id="toggle")
                    btn_toggle_sidebar.click(toggle_sidebar, [sidebar_state], [sidebar_left, sidebar_state])


                    model_label = 'TIN'
                    if model_label:
                        label_text = f"LLM Mode: | Model: {model_label}"

                    # Build ChatInterface
                    _ = gr.ChatInterface(
                        fn=None,
                        chatbot=gr.Chatbot(
                            label=label_text,
                            show_copy_button=True,
                            elem_id="chatbot",
                            avatar_images=(None),
                            render=False,
                        ),
                        additional_inputs=[
                            mode,
                            upload_button,
                            system_prompt_input,
                        ],
                    )

        return blocks

    # --- Public methods to get or mount the UI ---

    def get_ui_blocks(self) -> gr.Blocks:
        """Return the cached or newly built Gradio Blocks."""
        
        self._ui_block = self._build_ui_blocks()
        return self._ui_block



if __name__ == "__main__":
    ui = PrivateGptUi()
    demo = ui.get_ui_blocks()
    demo.launch()
