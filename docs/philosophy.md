# The "Why"

## Mission
Enable an operator to safely and efficiently control a simulated ROV in a deep sea trench off the coast of California. It will navigate to and collect a rare bioluminescent sea slug *Bathydevius caudactylus*, and return it to a collection pod.  

---

## Operator Goals
- Maintain situational awareness of all the key states of the ROV, such as power, thrusters, and the claw  
- Navigate reliably  
- Collect samples using the claw  
- Respond to abnormalities quickly  
- Prioritise safety of the ROV  

---

## Design Principles

### Attention as a Finite Resource
- Ensure the primary colour scheme is fully monochrome greyscale  
- Use colour sparingly to indicate alerts and warnings  

### Situational Awareness over “Interestingness”
- Prioritise clarity over “interestingness” (e.g., icons must stay simple and 2D)  
- Present data in context (e.g., present pressure alongside an indicator if it’s low, normal, or high)  

### Hierarchy of Information
- **Level 1:** Overall system view (health, alarms, mission status)  
- **Level 2:** Subsystem view (claw, navigation, propulsion)  
- *(Levels 3: individual subsystem elements, and 4: maintenance/configuration are out of scope for this simulation)*  

### Perception, Comprehension, Projection
- **Perception:** Make the data clear  
- **Comprehension:** Contextualise what is normal vs abnormal  
- **Projection:** Predict future states of the ROV and alert accordingly  