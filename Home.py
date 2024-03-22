import sys
import anthropic
import streamlit as st
from src.prompt import pre_prompt
import numpy as np
from stl import mesh  # pip install numpy-stl
import plotly.graph_objects as go
import subprocess
import re as regex
import os
import time

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 
ANYSCALE_ENDPOINT_TOKEN = st.secrets["ANYSCALE_ENDPOINT_TOKEN"]
#ANYSCALE_ENDPOINT_TOKEN = st.sidebar.text_input("API KEY", "",type="password")
file_path = "stl_files/obj.stl"
if os.path.exists(file_path):
    os.remove(file_path)



st.image("notebooks/cadscribe.png", width=75)

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

def stl2mesh3d(stl_mesh):
    # stl_mesh is read by nympy-stl from a stl file; it is  an array of faces/triangles (i.e. three 3d points) 
    # this function extracts the unique vertices and the lists I, J, K to define a Plotly mesh3d
    p, q, r = stl_mesh.vectors.shape #(p, 3, 3)
    # the array stl_mesh.vectors.reshape(p*q, r) can contain multiple copies of the same vertex;
    # extract unique vertices from all mesh triangles
    vertices, ixr = np.unique(stl_mesh.vectors.reshape(p*q, r), return_inverse=True, axis=0)
    I = np.take(ixr, [3*k for k in range(p)])
    J = np.take(ixr, [3*k+1 for k in range(p)])
    K = np.take(ixr, [3*k+2 for k in range(p)])
    return vertices, I, J, K
        


# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    if message["role"]=="user":
        avatar = "🧑"
    else:
        avatar = "🤖"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])


client = anthropic.Client(api_key=ANYSCALE_ENDPOINT_TOKEN)
if ANYSCALE_ENDPOINT_TOKEN is not None:
    if prompt := st.chat_input("For example try to create a helical gear or an airfoil specifying the NACA number"):
        with st.chat_message("user", avatar="🧑"):
            st.markdown(prompt)
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner():
                st.session_state.messages.append({"role": "user", "content": prompt})
                prompt = prompt + "Do not import any libraries"
                
                message_placeholder = st.empty()
                st.session_state['message_history'].append({"role": "user", "content": prompt})
                start = time.time()
                full_response = client.messages.create(
                    #model="claude-3-haiku-20240307",
                    #model="claude-3-sonnet-20240229",
                    model="claude-3-opus-20240229",
                    system=pre_prompt, # <-- system prompt
                    messages=st.session_state['message_history'],
                    max_tokens = 1000
                ).content[0].text
                print("RESPONSE:", full_response)


                    #message_placeholder.write(full_response)
                #message_placeholder.write(full_response)
                st.session_state['message_history'].append({
                            'role': 'assistant',
                            'content': full_response
                        })
                #st.session_state.messages.append({"role": "assistant", "content": full_response})
                
                script_name = "llm_query.py"
                with open(script_name, "w") as f:
                    sub1 = "```python"
                    sub2 = "```"
                    
                    test_str=full_response.replace(sub1,"*")
                    print(test_str)
                    test_str=test_str.replace(sub2,"*")
                    re=test_str.split("*")
                    code=re[1]
                    # Define a regex pattern to match import statements
                    pattern = r'\bimport\s+\w+\s*(?:as\s+\w+)?\b'

                    # Use re.sub() to replace all matches with an empty string
                    code = regex.sub(pattern, '', code)
                    if "parafoil" in full_response:
                        parafoil = "import parafoil"
                    else:
                        parafoil = ""
                    f.write(
                        f'\nimport cadquery as cq\nimport cq_gears\n{parafoil}\n{code}\
                            \ncq.exporters.export(obj, "stl_files/obj.stl")\
                            \ncq.exporters.export(obj, "stl_files/obj.step")'
                    )
                    
                #import llm_query
                subprocess.run([f"{sys.executable}", "llm_query.py"])

                stl_file_path = "stl_files/obj.stl"
                if os.path.exists(stl_file_path):
                    my_mesh = mesh.Mesh.from_file('stl_files/obj.stl')
                else:
                    my_mesh = mesh.Mesh.from_file('stl_files/fail.stl')

                vertices, I, J, K = stl2mesh3d(my_mesh)
                x, y, z = vertices.T
                colorscale= [[0, '#e5dee5'], [1, '#e5dee5']]                           
                mesh3D = go.Mesh3d(
                            x=x+10,
                            y=y,
                            z=z, 
                            i=I, 
                            j=J, 
                            k=K, 
                            flatshading=True,
                            colorscale=colorscale, 
                            intensity=z, 
                            name='AT&T',
                            showscale=False)
                layout = go.Layout(
                            width=800,
                            height=400,
                            scene_camera=dict(eye=dict(x=1.25, y=-1.25, z=1)),
                            scene_xaxis_visible=False,
                            scene_yaxis_visible=False,
                            scene_zaxis_visible=False,
                            scene=dict(
                                aspectmode='data'
                        ))
                fig = go.Figure(data=[mesh3D],
                                layout=layout
                                )
                fig.data[0].update(lighting=dict(ambient= 0.18,
                                                diffuse= 1,
                                                fresnel=  .1,
                                                specular= 1,
                                                roughness= .1,
                                                facenormalsepsilon=0))
                
                fig.data[0].update(lightposition=dict(x=3000,
                                                    y=3000,
                                                    z=10000))
                st.plotly_chart(fig, use_container_width=True)
        end = time.time()

        
        # Check if the file exists
        st.write(f"Generated in **{round(end-start, 2)}** seconds")
        if os.path.exists(stl_file_path):
            with open(stl_file_path, "rb") as file:
                btn = st.download_button(
                    label="Download STL",
                    data=file,
                    file_name="obj.stl",
                    mime="application/octet-stream"
            )
        


else:
    st.sidebar.warning("INPUT API KEY!")
