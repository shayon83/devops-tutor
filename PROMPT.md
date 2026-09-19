/openspec-explore I want to build a tutor web application using a LLM for inference and livekit for voice conversation. I can think of a few functional and non functional requirements but I'd like to explore more. This is something I have to submit for assessment and this is the submission format that has been requested:
Submit a **zip file of your git repository** (including the `.git` folder), uploaded directly to your application, containing:

1. **All source code** for frontend and backend.
2. **`PROMPT.md`** that contains this prompt exactly. 
3. **`README.md`** with:
    - Architecture overview (a short paragraph or simple diagram).
    - Key design decisions and tradeoffs.
    - A brief note on how you'd scale the system.
4. **`.env.example`** listing every environment variable needed to run the project (e.g., `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `LIVEKIT_URL`, LLM API keys, etc.). We will create our own `.env` from this template to run your project.
5. The project **must read all secrets and configuration from a `.env` file** in the project root. No hardcoded keys.
6. **`workflow.md`** describing your workflow, AI tools used, specific models, harnesses, and how you use them.
7. A short video walkthrough of the interface and agent functioning
Ignore 2 and 7 for now as I can handle them separately.
Keeping this in mind let's get started exploring the requirements for the app
