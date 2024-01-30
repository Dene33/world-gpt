# Story Generator

![cover](https://github.com/Dene33/world-gpt/assets/27821127/b8a09e3e-e79f-47ff-900e-cba31197738f)

World generation            |  NPC generation
:-------------------------:|:-------------------------:
![image_sg3](https://github.com/Dene33/world-gpt/assets/27821127/80a8e236-f22e-480b-bb3e-64fa4cc1d075)  |  ![image_sg2](https://github.com/Dene33/world-gpt/assets/27821127/3ef90956-bc66-43cf-a6a1-dd63bbe307b9)

Story Generator is an app, available as a [web version](https://www.story-generator.ai/) or a standalone for [Mac, Windows and Linux](https://github.com/Dene33/world-gpt/releases).

With ChatGPT as the backbone, create your own world and observe lifelike characters interacting with each other and living their lives. All that from a **single text input** with your world description! 

## Video demo

[![Watch the video](https://cdn.loom.com/sessions/thumbnails/8cd9860e343b43ad9d04a12055f16ee9-1705522236195-with-play.gif)](https://www.loom.com/embed/8cd9860e343b43ad9d04a12055f16ee9?sid=24642174-f674-4147-854f-eaf50fd791d2)

## Idea

OpenAI's ChatGPT blew my mind and I got an idea about using it as a tool for world generation. But static worlds are boring! So I decided to add NPCs (non-playable characters) to see if they can interact in the evolving worlds and achieve their goals... It turns out that yes, they can! And it's super interesting to observe how they do that and what happens to them. That's how the Story Generator was born.

## Features

- **World Creation:** Create custom worlds from any(!) description you can imagine. Whether it's a medieval dark fantasy realm or a cyber-punk sci-fi setting with cyber-ponies (yes! Cyber-ponies!), the possibilities are endless
  
- **Dynamic NPCs:** Each NPC within the generated world has its own unique name, attributes, global goal and current state. These characters are not mere placeholders but dynamic entities that react and adapt to the changing world around them
  
- **Evolving Worlds:** With the initial description provided, the generated worlds undergo changes over time based on a specified interval. Immerse yourself in the excitement of observing a dynamic world that continuously evolves and transforms
  
- **Changing World Characteristics:** Various aspects of the world, such as its temperature and environment, dynamically shift and transform. These changes trigger a chain of events that prompt the NPCs to respond and adapt, creating a dynamic and realistic narrative

- **Text-to-image Generation:** Generated textual descriptions of the world and characters are fed to the text-to-image (Dall-e 3 by default) model which generates wonderful images that support the story

Ultimately, the world's and NPC's conditions converge to create an exceptional story.

[Try it for free on the web](https://www.story-generator.ai/), [run it for free locally](https://github.com/Dene33/world-gpt/releases), or [buy it to support the creator](https://dene33.gumroad.com/l/story-generator?referrer=https%3A%2F%2Fwww.story-generator.ai%2Fpricing%2F&wanted=true). Story Generator is built entirely using [Shiny](https://shiny.posit.co/py/) so if you want to know how to build web apps with Shiny alongside ChatGPT in an asynchronous manner that's a great source of knowledge! Additionally, you can employ Story Generator in your own game by customizing the code to suit your requirements.

## Install from source
1. Clone the repo
2. Create a Python 3.10 environment, here is how you can do it with conda `conda create -n worldgpt python=3.10.6`
3. Install all the requirement packages with `pip install -r requirements.txt`
4. Finally run the app with `python ./story_generator.py`
5. Provide your OpenAI key. [See here](https://help.openai.com/en/articles/4936850-where-do-i-find-my-api-key). This repo doesn't contain the OpenAI key. If you want to try it for free, visit https://www.story-generator.ai/ It might be available if the usage of my openai key has not exceed the limits :) 

## TODO
1. ~~Text-to-image generation~~
2. Generate the full story from the whole world's and NPCs' progress
3. ~~Allow user to manually adjust the world's and NPCs' state on the fly~~
4. ~~Save/load~~
5. Track for NPCs' goal completion, keep memory of completed tasks, select new one(s)

## Support the author :heart:
It really matters! At least it will allow to support the free web-version of the app (hosting, openai requests)

[Ko-Fi](https://ko-fi.com/dene33)

[GitHub sponsorship](https://github.com/sponsors/Dene)

[Gumroad](https://dene33.gumroad.com/l/story-generator?referrer=https%3A%2F%2Fwww.story-generator.ai%2Fpricing%2F&wanted=true)

