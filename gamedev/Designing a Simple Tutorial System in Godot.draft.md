# Designing a Simple Tutorial System in Godot

```
scaffold : 
- intro, introduce what I am building
- one paragraph about the 'problem to solve'
- talk about the "goal" of the system and why I am building it
  - mostly 'cause I wanted to create one component / see what I could do
- quick bullet list with overview
- section about data modeling
- section about the UI component
- section about the trigger/queue/requirement system
  - mention the two explored ideas
- wiring everything up
- demonstration plus closing thoughts
```

Greetings, fellow traveler. Do you want to create your own tutorial system for your game ? A simple, dialog-style, configurable, tutorial system ? 

In this blog post, I write about developing the tutorial system from scratch in Godot (and GDScript) for my own game - NanoSwarm : Dominion. Not just the "final result", but the thought process behind each step, what worked and what didn't, and general useful tricks applicable in other scenarios.

<!-- insert cover image here -->

There are multiple ways of designing an in-game Tutorial, from dedicated tutorial levels to NPC characters that explain a given mechanic out to the player. For my game, I decided to present tutorials using a "dialog-style" UI that may show up when starting a new level or encountering a new enemy.

Creating one tutorial in this manner is a simple-enough matter. All it would take is to create the needed UI elements, write out the text I want to show and make it pop up when entering the `Scene`. *However*, once I want to create multiple different tutorial dialogs and I want to show them at different times, across different `Scenes` in Godot it quickly transforms into a jumbled mess.

So, to prevent that, let's design something that's both simple to use and flexible to support my needs (and hopefully yours). 

After creating two or three different tutorials "manually" and comparing them with each other, we notice a pattern. Every tutorial can have the same **visuals**, with only the **content** being truly unique and with some common **rules** as to when they should trigger. 

With this in mind, I decided to split the system in three components :
- the **TutorialData** : A `Resource` that holds the data for a given Tutorial
- the **TutorialDialog** : A `Control` scene responsible to display **TutorialData** to the player
- the **Decision-Making System** : A `Script` containing logic that will dictate when a Tutorial should be shown

With this system implemented, I am able to focus on writing down different tutorials in their own `Resource` files and having them show up when I want to, without having to shuffle through all my game's files to see where I should do something or not.

On the following sections, I'll do my best to explain "how" I implemented each component as well as the "why" behind some core decisions. All of the components can (and should!) be customized to fit a game's specific needs. 

## Modeling a Custom Resource for Tutorial Data

"TutorialData" custom resource
core fields : id, steps array (step also extends resource; each with "text" element)
- step (sub) resource, when declared inside the base TutorialData Resource, works just fine in code
- however, when trying to create the base TutorialData via Inspector panel, adding a new step doesn't work via editor
- with a standalone resource (separate file), works without issue
- it *can* be made to work, if need be, by adding a custom button to the exported properties (and tagging the resource with @tool) that, on click, adds the correct instance to the array
save/retrieve using ResourceSaver and ResourceLoader
can be "managed" in a singleton (autoload, in Godot) for easy access
mention utility dictionary to track which tutorial as been seen or not (id, bool)


## Creating the Tutorial Dialog UI Component

(check devlog#14)

mention the add child vs instantiate child issue (start at the @onready props problem)

mention the difference between packed scene "instantiate" method vs. instance placeholder "create_instance" method
- "instantiate" **does not** call the _ready method (only when adding the instance to the scene tree via add_child)
- "create_instance" **does** call the _ready method and already adds the instance to the scene tree (no add_child needed)


## Setting up the Decision-Making System (with two variations)

base idea :
- create the multiple instances of "TutorialData"
- when entering a level, find out which ones to show
  - this point I had 2 ideas
- add the "to show" tutorials on a shared (utility) array
- at specific moments / intervals in the level, check if I have a tutorial to show
  - mention generic use cases
  - mention my use case : after transitioning to a new state in the city

version 1 : concentrate the logic on the TutorialData Resource
- added new fields : requirement(string), trigger (enum)
- goal : cycle through unseen tutorials when "needed" (my case : for a new level) > store relevant ones for later
- on level gen : find relevant tutorials for the level context > store those > save the ids in the level savefile
- on level load : get tutorials by id in savefile > filter by unseen ones > store those for later
- on state transition, check if there are stored tutorials with matching trigger. show those
- pro : more powerful; con : more "front heavy" (needs to cycle through all possible tutorials and evaluate expressions), requires to save in file for in-between loads

![version 1 sample 1](tutorial_system_approach1_1.png)
![version 1 sample 2](tutorial_system_approach1_2.png)
![version 1 sample 3](tutorial_system_approach1_3.png)
![version 1 sample 4](tutorial_system_approach1_4.png)

version 2 : have each entity hold which tutorials its linked to
- new custom resource : TutorialLink, with property id(string)
  - expected to contain an id of an existing tutorial
  - bonus : new wrapper Node TutorialLinkNode, with one TutorialLink export prop, to allow to "attach" a tutorial to any scenetree in the editor
  - explain the @tool usage
    - explain godot's validate property
  - explain the tutorial discovery on id set
- explain idea : when a regular entity (with one or more links) is instanced in the scene, each instanced link tries to also find (and add to the shared array)
- on state transition, try to pop a tutorial from the shared array and show if any. 
  - to support daisy chain, also do the check on tutorial end 
- pro : easy to use, once set up; con : hard to set up, less powerful with the conditions to show the tutorial

![version 2 sample 1](tutorial_system_approach2_1.png)
![version 2 sample 2](tutorial_system_approach2_2.png)
![version 2 sample 3](resource_exported_prop_dynamiclist_inspector.png)
![version 2 sample 4](resource_exported_prop_dynamiclist_script.png)

## The Final Result

