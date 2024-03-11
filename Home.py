import sys
import openai
import streamlit as st
from src.prompt import pre_prompt
import numpy as np
from stl import mesh  # pip install numpy-stl
import plotly.graph_objects as go
import subprocess


ANYSCALE_ENDPOINT_TOKEN = st.sidebar.text_input("API KEY", "",type="password")


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


class OpenAIChatAgent:
    def __init__(self, model: str):
    #In this simple example, we do not modify the past conversation.
    #Eventually you will run out of context window, but this should be enough for a 30-step conversation
    #You need to either trim the message history or summarize it for longer conversations
        self.message_history = []
        self.model = model 
        self.oai_client = openai.OpenAI(
           api_key=ANYSCALE_ENDPOINT_TOKEN,
           #base_url = "https://api.endpoints.anyscale.com/v1",

        )
    def greet(self):
        return None

    def process_input(self, input: str):
        if len(st.session_state['message_history']) == 0:
            st.session_state['message_history'].append(
                {
                    'role': 'user',
                    'content': pre_prompt
                }
            )

        body = {
                    'role': 'user',
                    'content': input
                }
        
        st.session_state['message_history'].append(body)
        
        response = self.oai_client.chat.completions.create(
           
           model = self.model,
           messages = st.session_state['message_history'],
           stream = True,
           temperature =  0.01
        )
        words = ''
        for tok in response: 
            delta = tok.choices[0].delta
            if not delta: # End token 
                break
            elif delta.content:
                words += delta.content
                yield delta.content 
            else: 
                continue
        


# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


agent = OpenAIChatAgent("gpt-3.5-turbo")
#agent = OpenAIChatAgent(model = "mistralai/Mixtral-8x7B-Instruct-v0.1")
if ANYSCALE_ENDPOINT_TOKEN is not None:
    
    if prompt := st.chat_input("What is up?"):
        # if len(st.session_state.messages) == 0:
        # else:
        
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        prompt = "Do not import any libraries, write everything in a codeblock: " + prompt
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
        for word in agent.process_input(prompt):
            full_response += word
            message_placeholder.write(full_response + "▌")
        message_placeholder.write(full_response)
        st.session_state['message_history'].append({
                    'role': 'assistant',
                    'content': full_response
                })
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        print(st.session_state['message_history'])
        script_name = "llm_query.py"
        with open(script_name, "w") as f:
            sub1 = "```python"
            sub2 = "```"
            
            test_str=full_response.replace(sub1,"*")
            print(test_str)
            test_str=test_str.replace(sub2,"*")
            re=test_str.split("*")
            code=re[1]
            f.write(
                f'\nimport cadquery as cq\n{code}\ncq.exporters.export(obj, "stl_files/obj.stl")'
            )
            
        #import llm_query
        import llm_query


        my_mesh = mesh.Mesh.from_file('stl_files/obj.stl')
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
        
        st.session_state.messages.append({"role": "assistant", "content": st.plotly_chart(fig)})

else:
    st.sidebar.warning("INPUT API KEY!")