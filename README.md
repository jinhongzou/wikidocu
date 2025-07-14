## 📌 WikiDocu

### English| [简体中文](README_zh-CN.md) 

WikiDocu is a document analysis tool built on **langchain**, designed to help users extract key information from local files and leverage large language models (LLMs) to intelligently understand and answer research topics or questions. It is suitable for quickly reviewing technical documents, research reports, project specifications, and other textual content.

Unlike traditional **RAG (Retrieval-Augmented Generation)** systems, WikiDocu does not rely on vector databases or semantic search. Instead, it uses the contextual understanding capability of LLMs to directly analyze and extract relevant information from user-provided documents, generating structured answers around the input query.

#### 😊 Example:  
Suppose you have a project containing `.md` documentation files and multiple `.py` code files. The `.md` files provide comprehensive explanations including function descriptions, parameter interpretations, and invocation examples, while the `.py` files contain the actual source code implementing these APIs, complete with comments for better understanding.

💬 Now, you want to find out how to create a Pydantic model instance. Here are two different workflows:

✅ **Traditional RAG System Workflow:**  
1. **Preprocessing Phase:** Convert all documents into vector representations and store them in a vector database.  
2. **Query Phase:** The user inputs a query like "How to create a Pydantic model instance." The system generates a vector representation of the query and searches the vector database for the most similar document segments ⚠️.  
3. **Result Presentation:** The system returns the most relevant document fragments and may use an LLM to further summarize these results.

✅ **WikiDocu Workflow:**  
1. **Document Loading:** Select and load all `.md` and `.py` files from the technical documentation directory.  
2. **Input Query:** The user enters the question "How to create a Pydantic model instance" via the web interface.  
3. **Direct Analysis:** The LLM reads and understands the entire document content, identifying relevant information sections 📝.  
4. **Answer Generation:** Based on the context, the LLM generates a structured response. For example:  
   ```python
   class PydanticAgetn():
       ...
   ```

🌐 Web Interface

**Advantages of this approach:**  

- ✅ **No additional indexing required:** No need to build a vector database, saving time and resources.
- ✅ **Simplified deployment:** Reduced system complexity makes deployment faster and easier.
- ✅ **More natural responses:** Answers are generated based on full-text understanding, making them more aligned with user needs.

**Key Features:**  

- 📁 Supports loading various document formats from a local directory: currently supports only `[".py", ".md", ".txt"]`.
- 💬 After the user inputs a research topic, the LLM directly analyzes the relevant documents and provides a summarized response.
- 🧠 No need to build a knowledge base index or use vector embeddings—easy deployment and fast response times.
- 📝 Supports Markdown formatting for result presentation, enhancing readability and reusability.

This tool is ideal for lightweight document Q&A, technical reference assistance, and personal knowledge organization scenarios.

🧰 Tech Stack  
WikiDocu is built using the following core technologies, ensuring ease of use and extensibility:

| Technology/Framework | Purpose |
|----------------------|---------|
| Python 3.10+         | Primary development language with full type support and modern syntax |
| Shiny for Python     | Build interactive web interfaces for visualizing user input and output results |
| Pydantic             | Data model definition and validation, improving code robustness and readability |
| Markdown             | Optional: Parse Markdown format for front-end display, enhancing visual appeal |
| langchain            | Integrate LLM chain calls, simplifying LLM task workflows |
| LLM API (OpenAI / SiliconFlow / Self-hosted) | Provide high-performance LLM inference services responsible for core content understanding and response generation |
| asyncio              | Asynchronous programming support, improving multi-file processing and network request efficiency |

🔎 Why Use LLM-Driven Processing?  
The design philosophy of WikiDocu is to fully utilize the powerful contextual understanding and generalization capabilities of large language models, avoiding complex retrieval and vectorization processes. Compared to traditional RAG architectures, this approach offers the following benefits:

- ✅ No need to build indexes or vector databases, reducing deployment costs.
- ✅ Fewer intermediate steps, lowering system complexity.
- ✅ More naturally incorporates user intent, producing context-aware responses.

⚠️ **Limitation:**受限于 LLM 上下文长度，一次分析的文档总量有限.  
非常适合轻量级本地文档问答、快速原型验证等场景。

📁 Project Structure
```
wiki-docu/
├── src/
│   └── filecontentextract.py       # Core logic: call LLM to extract document content
│   └── directorytreegenerator.py   # Directory tree generation
│   └── models.py                   # Data models
│   └── prompts_zh.py               # Prompt templates
├── frontend/
│   └── utils.py                    # Frontend utility functions: report generation, UI components, etc.
├── docs/                           # Default scan directory, stores copied documents
├── app_wikidocu.py                 # Main application entry point
├── cli_wikidocu.py                 # Command-line interface entry point
├── README.md                       # This file
└── requirements.txt                # List of dependencies
```

🚀 Quick Start  
1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**  
   Before running, ensure the following environment variables are set (or modify default values in `app.py`):

   ```bash
   export MODEL_NAME="Qwen/Qwen2.5-7B-Instruct"
   export OPENAI_BASE_URL="https://api.siliconflow.cn/v1"
   export OPENAI_API_KEY="your_api_key_here"
   ```

3. **Launch the Application**

   **Option 1: Web App Mode**
   ```bash
   python app_wikidocu.py
   ```
   Visit the provided URL (usually http://127.0.0.1:8000) to access the web interface.

   **Option 2: CLI Mode**
   ```bash
   python cli_wikidocu.py
   ```

🧪 Functionality Overview  
- **wikidocu:** Main output area displaying the final analysis report.  
- **Search Results:** Detailed output showing raw extracted document snippets.  
- **Input Box:** Enter your question, then click "Search" to execute.

📦 Key Dependencies  
```plaintext
langchain_core==0.3.67
langgraph==0.5.0
pydantic==2.10.6
shiny==1.4.0 
```

🤝 Contribution Guidelines  
We welcome Issues and Pull Requests! Please follow this workflow:  

1. Fork the repository.  
2. Create a new branch (`git checkout -b feature/new-feature`).  
3. Commit changes (`git commit -m 'Add some feature'`).  
4. Push to the branch (`git push origin feature/new-feature`).  
5. Open a Pull Request.

📜 License  
MIT License – see the LICENSE file.
