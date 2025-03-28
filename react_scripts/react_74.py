import requests
import re
import ollama
import networkx as nx
 
def react_74(full_name):

    token = "github_token"
    headers = {"Accept": "application/vnd.github.v3+json", "Authorization": f"token {token}"}
    
    repo_url = f"https://api.github.com/repos/{full_name}"

    api_patterns = ["controllers/", "routes/", "api/", "handlers/"]
    service_patterns = ["services/", "utils/", "helpers/"]
    test_patterns = ["tests/unit/", "tests/integration/", "tests/functional/"]
    dependency_files = ["package.json", "requirements.txt", "pom.xml"]
    
    response = requests.get(f"{repo_url}/contents", headers=headers)
    if response.status_code == 200:
        repo_files = [file["download_url"] for file in response.json()]
    else:
        repo_files = []
    
    source_code = {}
    for url in repo_files:
        if url != None:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                source_code[url] = response.text

    findings = {
        "api_modules": [],
        "service_modules": [],
        "test_structure": [],
        "dependency_issues": [],
        "monolithic_files": [],
        "circular_dependencies": []
    }

    for file, content in source_code.items():
        if any(pattern in file for pattern in api_patterns):
            findings["api_modules"].append(file)

        if any(pattern in file for pattern in service_patterns):
            findings["service_modules"].append(file)

        if any(pattern in file for pattern in test_patterns):
            findings["test_structure"].append(file)

        if len(content.split("\n")) > 500:  
            findings["monolithic_files"].append(file)

        if any(dep_file in file for dep_file in dependency_files):
            findings["dependency_issues"].append((file, content))

    dependency_graph = nx.DiGraph()
    imports = {}
    for file, content in source_code.items():
        matches = re.findall(r'^\s*(?:import|from)\s+([\w.]+)', content, re.MULTILINE)
        imports[file] = matches
        for imp in matches:
            dependency_graph.add_edge(file, imp)

    try:
        cycle = nx.find_cycle(dependency_graph)
        findings["circular_dependencies"] = cycle
    except nx.NetworkXNoCycle:
        cycle = None        
    
    query = f"""Analyze the following GitHub repository for modularization best practices.
    API Modules Detected: {len(findings["api_modules"])}.
    Service/Utility Modules Detected: {len(findings["service_modules"])}.
    Test Structure: {findings["test_structure"]}
    Potential Monolithic Files: {findings["monolithic_files"]}
    Circular Dependencies Found: {findings["circular_dependencies"]}
    Dependency Issues: {findings["dependency_issues"]}

    Based on your analysis, just reply with a True if the repository ensures
    1. files structured properly into separate modules (e.g., controllers, services, routes)
    2. test files well-structured into unit/integration tests
    3. no unnecessary or outdated dependencies in `package.json`, `requirements.txt`, or `pom.xml`
    4. no large, unmodularized files that should be refactored
    5. no circular dependencies
    and False otherwise. Remember, only reply with True or False."""

    response = ollama.chat(model="llama3:8b", messages=[{"role": "user", "content": query}])
    return response['message']['content']

print(react_74("public-apis/public-apis")) 
