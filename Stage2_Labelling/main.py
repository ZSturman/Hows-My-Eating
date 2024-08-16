from fasthtml.common import *
from fasthtml.fastapp import *
from fastcore.xml import *
from fastcore.utils import *
from utils.video_converter import convert_to_mp4


# Initialize FastHTML
app, rt = fast_app()

# Define headers (for Tailwind CSS and HTMX)
headers = [
    Script(src="https://cdn.tailwindcss.com/"),
    Script(src="https://unpkg.com/htmx.org@1.4.1"),
]


data_directory = "public/data"

# function that finds all .mov files in teh data directory and converts them using convert_to_mp4(MOV, MP4)
def convert_all_mov_files():
    print("Converting all .mov files to .mp4")
    for file in os.listdir(data_directory):
        if file.endswith(".mov"):
            print(f"Converting {file} to .mp4")
            convert_to_mp4(f"{data_directory}/{file}", f"{data_directory}/{file.replace('.mov', '.mp4')}")
            
#convert_all_mov_files()

video_to_play = "public/data/1723707479.70642.mov"
#video_to_play = "public/vidTest.mp4"


# State management (simple approach, you might need to handle this differently)
mouth_actions = ["Eating", "Drinking", "Talking"]
body_actions = ["Walking", "Sitting", "Standing"]

def custom_video_player(video_url):
    video = Video(
        src=video_url, 
        type="video/mp4",
        controls=True,
        id="vid",
        hx_trigger="click",
        hx_target="#vid",
        #autostart=True,
        #preload="auto",
    )
    
    return video

def action_buttons(actions):
    return Div(
        *[
            Button(
                action, cls="h-10 rounded-lg border-[1px] border-zinc-700 w-40"
            )
            for action in actions
        ],
        _class="flex flex-row gap-2"
    )

@rt("/")
def get():
    return Html(
        *headers,
        Div(
            H1('Chew Labeller', cls="text-3xl text-center"),
            Div(
                Div("Current labels", cls="h-20 w-full text-center"),
                Div(
                    Div(
                        Div(
                            custom_video_player(video_to_play),
                            Div(
                                Button("play", _class="h-10 w-80 rounded-lg border-[1px] border-zinc-700"),
                                Button("pause", _class="h-10 w-80 rounded-lg border-[1px] border-zinc-700"),
                                _class="controls"
                            ),
                            _class="w-full flex flex-col items-center justify-evenly"
                        ),
                        _class="flex flex-col w-full h-full"
                    ),
                    Div(
                        action_buttons(body_actions),
                        action_buttons(mouth_actions),
                        _class="flex flex-col w-2/5 gap-10 h-full"
                    ),
                    _class="h-full w-full text-center flex justify-between"
                ),
                _class="w-full h-full flex flex-col pt-10"
            ),
            _class="w-full h-full"
        )
    )


serve()