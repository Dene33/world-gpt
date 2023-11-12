# Story Generator

![image](https://github.com/Dene33/world-gpt/assets/27821127/8a3384a4-0000-46ff-a4ea-b6fefbd7378c)

Story Generator is a groundbreaking app that brings your imagination to life. Input your world description, and watch as an entire universe unfolds before your eyes. With ChatGPT as the backbone, witness the progression of your world and observe lifelike NPCs as they navigate their intricacies. Experience the joy of creation in real-time, all within the palm of your hand.

## Idea

OpenAI's ChatGPT blew my mind and I got an idea about using it as a tool for world generation. But static worlds are boring! So I decided to add NPCs (non-playable characters) to see if they can interact in the evolving worlds and achieve their goals... It turns out that yes, they can! And it's super interesting to observe how they do that and what happens to them. That's how the Story Generator was born.

## Features

- **World Creation:** Create custom worlds from any(!) description you can imagine. Whether it's a medieval dark fantasy realm or a cyber-punk sci-fi setting with cyber-ponies (yes! Cyber-ponies!), the possibilities are endless
  
- **Dynamic NPCs:** Each NPC within the generated world has its own unique name, attributes, global goal and current state. These characters are not mere placeholders but dynamic entities that react and adapt to the changing world around them
  
- **Evolving Worlds:** With the initial description provided, the generated worlds undergo changes over time based on a specified interval. Immerse yourself in the excitement of observing a dynamic world that continuously evolves and transforms
  
- **Changing World Characteristics:** Various aspects of the world, such as its temperature and environment, dynamically shift and transform. These changes trigger a chain of events that prompt the NPCs to respond and adapt, creating a dynamic and realistic narrative

Ultimately, the world's and NPC's conditions converge to create an exceptional story.

[Try it for free](https://www.story-generator.ai/) or [buy it](https://dene33.gumroad.com/l/story-generator?referrer=https%3A%2F%2Fwww.story-generator.ai%2Fpricing%2F&wanted=true) as a standalone app. The latter option includes the complete source code and requires a one-time payment only (no subscriptions!). Story Generator is built entirely using [Shiny](https://shiny.posit.co/py/) so if you want to know how to build web apps with Shiny alongside ChatGPT in an asynchronous manner that's a great source of knowledge! Additionally, you can employ Story Generator in your own game by customizing the code to suit your requirements.

## Install from source
1. Clone the repo
2. Create a Python 3.10 environment, here is how you can do it with conda `conda create -n worldgpt python=3.10.6`
3. Install all the requirement packages with `pip install -r requirements.txt`
4. Finally run the app with `python ./story_generator.py`
5. Provide your OpenAI key. [See here](https://help.openai.com/en/articles/4936850-where-do-i-find-my-api-key). This repo doesn't contain the OpenAI key
