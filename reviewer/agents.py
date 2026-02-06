
import logging
import sys
import ollama

# This Adapter allows the UI to use the Ollama library directly
# It serves as a reliable bridge to your backend.

class BaseAgent:
    def __init__(self, model_name, temperature=0.3):
        self.model_name = model_name
        self.temperature = temperature

    def call_ollama(self, prompt, system_prompt=""):
        try:
            response = ollama.generate(
                model=self.model_name,
                prompt=prompt,
                system=system_prompt,
                options={
                    "temperature": self.temperature,
                    "num_ctx": 8192
                }
            )
            return response['response']
        except Exception as e:
            return f"Error calling AI model ({self.model_name}): {e}"

class CriticAgent(BaseAgent):
    def review_manuscript(self, text, vision_context, manuscript_type, study_design, has_ai):
        system_prompt = (
            "You are a strict, senior academic peer reviewer. "
            "Critically evaluate this manuscript."
        )
        
        # Construct the context
        prompt = f"### MANUSCRIPT TEXT ###\n{text[:28000]}\n\n"
        
        if vision_context and "No figure" not in vision_context:
            prompt += f"### VISUAL ANALYSIS ###\n{vision_context}\n\n"
            
        prompt += f"### METADATA ###\nType: {manuscript_type}\nDesign: {study_design}\n"
        
        if has_ai:
            prompt += "Includes AI/ML: YES (Check for CLAIM/equator-network standards).\n"
            
        prompt += "\n### TASK ###\nProvide a comprehensive critique focusing on methodology, rigor, and clarity."
        
        print("   (Critic is thinking...)")
        return self.call_ollama(prompt, system_prompt)

class WriterAgent(BaseAgent):
    def draft_review(self, critique, manuscript_type):
        system_prompt = "You are a professional medical editor. Draft a formal peer review report."
        
        prompt = (
            f"### CRITIQUE NOTES ###\n{critique}\n\n"
            f"### TASK ###\n"
            f"Draft a formal peer review for a {manuscript_type}."
        )
        
        print("   (Writer is drafting...)")
        return self.call_ollama(prompt, system_prompt)

class VisionAgent(BaseAgent):
    def analyze_figures(self, image_paths):
        full_report = []
        for i, img_path in enumerate(image_paths):
            try:
                print(f"   (Looking at image {i+1}/{len(image_paths)}...)")
                res = ollama.generate(
                    model=self.model_name,
                    prompt="Describe this scientific figure. Are the labels clear? Are there errors?",
                    images=[str(img_path)],
                    options={"temperature": 0.1}
                )
                full_report.append(f"### Figure {i+1} Analysis ###\n{res['response']}")
            except Exception as e:
                full_report.append(f"### Figure {i+1} ###\nError: {e}")
        return "\n\n".join(full_report)
