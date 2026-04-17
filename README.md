[EVERYWHERE = NOWHERE = NOW] Proposal Documentation


Victoria Hoang 


Kiana Rezaee 


CART360 - Tangible Media & Physical Computing


Elio Bidinost


[1] Github & Website

Website: 
Website repository: https://github.com/DUZAKH/CART360-documentation
Website link: https://duzakh.github.io/CART360-documentation/index.html


[2] Project Description

Context & Environment
Our project will be presented in a small dimly lit space in which participants can focus on the artifact without many distractions. The environment will ideally allow the object’s soft qualities (sounds, glowing body, and subtle movements) stand out and encourage participants to approach it with curiosity and playfulness. This installation is open to anyone, but particularly targets individuals interested in an all-encompassing sensory experience, exploring textures, light, and sound.
Relationship Between Users and the Artifact
The artifact seeks to form an intimate and playful relationship with participants, redefining one’s typical approach to technology. The soft robotic organism encourages users to engage with it both physically and emotionally by responding to touch and movement in ways that highlight empathy towards non-human beings. In depicting technology and devices as emotive and approachable beings, this project seeks to challenge preconceived notions of digital artifacts as cold and threatening. 
Empowerment
By offering a variety of playful and tangible interactions, this installation empowers users to explore technology with curiosity, touch, and engaged sense within a space that rewards experimentation. Participants are challenged to reconsider their relationship with technology as something beyond a service or a ‘means to’. They are encouraged to slow down, observe, and engage in tangible conversation with a being that isn’t conventionally categorized as a being from an anthropocentric view.
Interaction Design Strategies
The primary interaction design strategy for this project is to create a regulating system in which a linear input system (ultrasonic sensor) provides input to a self-regulating system (servo-motor and sound). This is a 0-1 system in which the sensor disturbs the self-regulating system, which in turn responds. The self-regulating component allows the artifact to respond adaptively, which gives participants a sense of sentience and conversation. 

The system components are:

Input: Ultrasonic sensor detects proximity of participants and provides a continuous stream of this distance data
Output: Servo motor rotates, curling the tentacles inwards around the participant, a direct response to their presence
Sound feedback: Rotation data sent to MaxMSP to generate real-time sound

The system is designed to craft a dynamic feedback loop in which participants’ movements affect the artifact, which in turn responds through motion and sound, encouraging participants to further explore in different ways, via touch or distance, while the system continuously responds. The project’s goal is to express technology as empathetic and approachable and reflects on current human-computer relationships.

In terms of other interactions, there will be a high dependence on the tactile aspects of the project. Materials are TPU, soft bioplastic, fabric, and silicone. In terms of light, we are thinking of using LEDs and using fibre optics and cotton to disperse it alongside the body of the object. We are also planning to explore including water in pipes throughout our project. . 
[3] Sensors
Our project’s prototype relies on an ultrasonic distance sensor (HC-SR04) to detect participants’ proximity to the artifact, enabling it to respond dynamically to physical presence. The sensor translates realtime distance into movement and sound, creating a tangible and realtime interaction that encourages playful engagement. The sensor is connected to a servo motor that slowly rotates 180 degrees which in turn controls wires passing through the artifact’s tentacles, creating an inward & outward curling motion. The rotation data of the servo motor is sent to MaxMSP via OSC to generate a soundscape, crafting an interaction that is not only visual, but tactile and auditory as well, pushing participants to perceive the artifact as sentient and expressive. Overall, the being responds to others in a manner that seeks intimacy and interaction. The system affords approachable and playful interaction, allowing participants to intuitively explore the artifact at their own pace. Ideally we would like to add photosensors to each leg of the project, allowing it to be in direct interaction with the reach of the audience member. 

[4] Interaction Design Strategy

The interaction design strategy for this project centers on creating a coupled cybernetic feedback loop between participants and the artifact. The system operates as a responsive organism that continuously senses, reacts, and adapts to user presence. The artifact behaves as a self-regulating multisensory system, encouraging participants to perceive it as an expressive being. Firstly, this system is made up of sensing, actuation, touch and audiovisual aspects to form a proximity based  interaction. This creates a sense that it is aware and interested in nearby humans. Secondly, the tactical interaction with the softness of the materials creates the illusion of empathy and approachability . 
Ultimately, the interaction strategy aims to slow participants down and encourage them to reconsider their relationship with technology. By responding gently and expressively to human presence, the artifact frames technology not as a tool but as an interactive being capable of emotional and sensory dialogue.
The following journey map/storyboard showcases what would happen in an interaction with our object. The audience is introduced to the hanging object, which is already showcasing slight movement. Upon their entry light and sound as well as other interactions begin to increase. This includes come hither motions if the audience is far and holding on if it's touched. 

[5] Similar Projects
[A] The Coral Morph by Xinyi Huang & Daniela M. Romano
Coral Morph is a moving textile installation that encourages emotional regulation and sensory engagement via soft robotics material movements. It includes touch sensors and heart-rate tracking to dynamically control inflatables. When participants either touch or breathe near the artifact, its main body as well as its surrounding tentacle-like tubes respond by changing shape and colour, seeking to elicit serenity. The installation was studied with 55 participants, who found it to be safe, interesting, and emotionally intelligent due to its tactile responses and organic movement.


[B] In Love With the World by Anicka Yi
In Love With the World is a large-scale installation of ‘aerobes’ that are bulbous robotic creatures resembling jellyfish that float autonomously in the space. It uses electronic tracking to respond to people and the overall environment and further engage smell via changing scentscapes. By combining organic form with robotics, this work seeks to question how machines could inhabit the world.
[C] Spirobs by Zhanchi Wang, Nikolas Ferris, and Xi Wei
SpiRobs are soft robots inspired by natural appendages like octopus arms and elephant trunks, which often follow a logarithmic spiral shape. The robots are 3D printed with flexible material and controlled by two or three cables that allow the body to curl and uncurl. This spiral movement lets the robot reach, wrap around, and grasp objects of different shapes and sizes using its flexible body. The design is simple, low-cost, and scalable, with versions ranging from tiny robots that can handle delicate organisms to larger robots capable of lifting heavy objects or operating on drones.
Comparison
Our starting point was projects like C-Spirob, wherein the ideas of less human robots can lead to breakthroughs in techn;logy. However, what we want to address is a tendency to stray from the aesthetics that inspire these objects. In this case we plan to highlight materials and aesthetics associated with the sea. Similarly, installations like B-Coral Morph and In A-Love With the World explore emotional engagement through responsive environments and organic forms. These works demonstrate how technology can behave in ways that feel alive and responsive. Our project draws inspiration from these approaches by emphasizing softness, tactility, and sensory feedback. Unlike these projects, however, our installation specifically aims to evoke empathy. We choose to approach it in the same way as Coral Morph, using  the aesthetics and material qualities of marine life. Through this combination of cybernetic interaction, soft robotics, and ocean-inspired aesthetics, the project explores how technology can be perceived not as a tool, but as a living presence capable of forming a gentle and curious relationship with participants.



Resources

Zhanchi, Nikolaos M. Freris, and Xi Wei. "SpiRobs: Logarithmic spiral-shaped robots for versatile grasping across scales." Device 3, no. 4 (2025).

