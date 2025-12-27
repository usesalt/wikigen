import os
import time
import yaml
from pocketflow import Node, BatchNode
from wikigen.utils.crawl_github_files import crawl_github_files
from wikigen.utils.call_llm import call_llm
from wikigen.utils.crawl_local_files import crawl_local_files
from wikigen.formatter.output_formatter import (
    Icons,
    print_phase_start,
    print_operation,
    print_success,
    print_phase_end,
    format_size,
)


# Helper to get content for specific file indices
def get_content_for_indices(files_data, indices):
    content_map = {}
    for i in indices:
        if 0 <= i < len(files_data):
            path, content = files_data[i]
            content_map[f"{i} # {path}"] = (
                content  # Use index + path as key for context
            )
    return content_map


class FetchRepo(Node):
    def prep(self, shared):
        repo_url = shared.get("repo_url")
        local_dir = shared.get("local_dir")
        project_name = shared.get("project_name")

        if not project_name:
            # Basic name derivation from URL or directory
            if repo_url:
                project_name = repo_url.split("/")[-1].replace(".git", "")
            else:
                project_name = os.path.basename(os.path.abspath(local_dir))
            shared["project_name"] = project_name

        # Get file patterns directly from shared
        include_patterns = shared["include_patterns"]
        exclude_patterns = shared["exclude_patterns"]
        max_file_size = shared["max_file_size"]

        return {
            "repo_url": repo_url,
            "local_dir": local_dir,
            "token": shared.get("github_token"),
            "include_patterns": include_patterns,
            "exclude_patterns": exclude_patterns,
            "max_file_size": max_file_size,
            "use_relative_paths": True,
        }

    def exec(self, prep_res):
        start_time = time.time()

        if prep_res["repo_url"]:
            print_phase_start("Repository Crawling", Icons.CRAWLING)
            result = crawl_github_files(
                repo_url=prep_res["repo_url"],
                token=prep_res["token"],
                include_patterns=prep_res["include_patterns"],
                exclude_patterns=prep_res["exclude_patterns"],
                max_file_size=prep_res["max_file_size"],
                use_relative_paths=prep_res["use_relative_paths"],
            )
        else:
            print_phase_start("Directory Crawling", Icons.CRAWLING)
            result = crawl_local_files(
                directory=prep_res["local_dir"],
                include_patterns=prep_res["include_patterns"],
                exclude_patterns=prep_res["exclude_patterns"],
                max_file_size=prep_res["max_file_size"],
                use_relative_paths=prep_res["use_relative_paths"],
            )

        # Convert dict to list of tuples: [(path, content), ...]
        files_list = list(result.get("files", {}).items())
        if len(files_list) == 0:
            raise (ValueError("Failed to fetch files"))

        # Calculate total size
        total_size = sum(len(content) for _, content in files_list)
        elapsed = time.time() - start_time

        print_success(
            f"Complete ({len(files_list)} files, {format_size(total_size)})",
            elapsed,
            indent=1,
        )
        print_phase_end()

        return files_list

    def post(self, shared, prep_res, exec_res):
        shared["files"] = exec_res  # List of (path, content) tuples


class IdentifyAbstractions(Node):
    def prep(self, shared):
        files_data = shared["files"]
        project_name = shared["project_name"]  # Get project name
        language = shared.get("language", "english")  # Get language
        use_cache = shared.get("use_cache", True)  # Get use_cache flag, default to True
        max_abstraction_num = shared.get(
            "max_abstraction_num", 10
        )  # Get max_abstraction_num, default to 10

        # Helper to create context from files, respecting limits (basic example)
        def create_llm_context(files_data):
            context = ""
            file_info = []  # Store tuples of (index, path)
            for i, (path, content) in enumerate(files_data):
                entry = f"--- File Index {i}: {path} ---\n{content}\n\n"
                context += entry
                file_info.append((i, path))

            return context, file_info  # file_info is list of (index, path)

        context, file_info = create_llm_context(files_data)
        # Format file info for the prompt (comment is just a hint for LLM)
        file_listing_for_prompt = "\n".join(
            [f"- {idx} # {path}" for idx, path in file_info]
        )
        return (
            context,
            file_listing_for_prompt,
            len(files_data),
            project_name,
            language,
            use_cache,
            max_abstraction_num,
        )  # Return all parameters

    def exec(self, prep_res):
        start_time = time.time()
        (
            context,
            file_listing_for_prompt,
            file_count,
            project_name,
            language,
            use_cache,
            max_abstraction_num,
        ) = prep_res  # Unpack all parameters

        print_phase_start("LLM Analysis", Icons.PROCESSING)
        print_operation("Identifying abstractions...", Icons.PROCESSING, indent=1)

        # Add language instruction and hints only if not English
        language_instruction = ""
        name_lang_hint = ""
        desc_lang_hint = ""
        if language.lower() != "english":
            language_instruction = f"IMPORTANT: Generate the `name` and `description` for each abstraction in **{language.capitalize()}** language. Do NOT use English for these fields.\n\n"
            # Keep specific hints here as name/description are primary targets
            name_lang_hint = f" (value in {language.capitalize()})"
            desc_lang_hint = f" (value in {language.capitalize()})"

        prompt = f"""
For the project `{project_name}`:

Codebase Context:
{context}

{language_instruction}Analyze the codebase context.
Identify the top 5 to {max_abstraction_num} core most important abstractions for technical documentation that helps existing and new engineers understand the codebase.

For each abstraction, provide:
1. A concise `name`{name_lang_hint}.
2. A technical `description` explaining what it does, its responsibilities, and role in the system, in around 100 words{desc_lang_hint}.
3. A list of relevant `file_indices` (integers) using the format `idx # path/comment`.

List of file indices and paths present in the context:
{file_listing_for_prompt}

Format the output as a YAML list of dictionaries:

```yaml
- name: |
    Query Processing{name_lang_hint}
  description: |
    Handles incoming queries and routes them to appropriate handlers.
    Responsible for parsing, validation, and initial processing of user requests.{desc_lang_hint}
  file_indices:
    - 0 # path/to/file1.py
    - 3 # path/to/related.py
- name: |
    Query Optimization{name_lang_hint}
  description: |
    Optimizes query execution by analyzing patterns and caching results.
    Manages performance improvements and resource allocation for query processing.{desc_lang_hint}
  file_indices:
    - 5 # path/to/another.js
# ... up to {max_abstraction_num} abstractions
```"""
        response = call_llm(
            prompt, use_cache=(use_cache and self.cur_retry == 0)
        )  # Use cache only if enabled and not retrying

        # --- Validation ---
        yaml_str = response.strip().split("```yaml")[1].split("```")[0].strip()
        abstractions = yaml.safe_load(yaml_str)

        if not isinstance(abstractions, list):
            raise ValueError("LLM Output is not a list")

        validated_abstractions = []
        for item in abstractions:
            if not isinstance(item, dict) or not all(
                k in item for k in ["name", "description", "file_indices"]
            ):
                raise ValueError(f"Missing keys in abstraction item: {item}")
            if not isinstance(item["name"], str):
                raise ValueError(f"Name is not a string in item: {item}")
            if not isinstance(item["description"], str):
                raise ValueError(f"Description is not a string in item: {item}")
            if not isinstance(item["file_indices"], list):
                raise ValueError(f"file_indices is not a list in item: {item}")

            # Validate indices
            validated_indices = []
            for idx_entry in item["file_indices"]:
                try:
                    if isinstance(idx_entry, int):
                        idx = idx_entry
                    elif isinstance(idx_entry, str) and "#" in idx_entry:
                        idx = int(idx_entry.split("#")[0].strip())
                    else:
                        idx = int(str(idx_entry).strip())

                    if not (0 <= idx < file_count):
                        raise ValueError(
                            f"Invalid file index {idx} found in item {item['name']}. Max index is {file_count - 1}."
                        )
                    validated_indices.append(idx)
                except (ValueError, TypeError):
                    raise ValueError(
                        f"Could not parse index from entry: {idx_entry} in item {item['name']}"
                    )

            item["files"] = sorted(list(set(validated_indices)))
            # Store only the required fields
            validated_abstractions.append(
                {
                    "name": item["name"],  # Potentially translated name
                    "description": item[
                        "description"
                    ],  # Potentially translated description
                    "files": item["files"],
                }
            )

        elapsed = time.time() - start_time
        print_success(
            f"Found {len(validated_abstractions)} abstractions", elapsed, indent=2
        )

        return validated_abstractions

    def post(self, shared, prep_res, exec_res):
        shared["abstractions"] = (
            exec_res  # List of {"name": str, "description": str, "files": [int]}
        )


class AnalyzeRelationships(Node):
    def prep(self, shared):
        abstractions = shared[
            "abstractions"
        ]  # Now contains 'files' list of indices, name/description potentially translated
        files_data = shared["files"]
        project_name = shared["project_name"]  # Get project name
        language = shared.get("language", "english")  # Get language
        use_cache = shared.get("use_cache", True)  # Get use_cache flag, default to True

        # Get the actual number of abstractions directly
        num_abstractions = len(abstractions)

        # Create context with abstraction names, indices, descriptions, and relevant file snippets
        context = "Identified Abstractions:\\n"
        all_relevant_indices = set()
        abstraction_info_for_prompt = []
        for i, abstr in enumerate(abstractions):
            # Use 'files' which contains indices directly
            file_indices_str = ", ".join(map(str, abstr["files"]))
            # Abstraction name and description might be translated already
            info_line = f"- Index {i}: {abstr['name']} (Relevant file indices: [{file_indices_str}])\\n  Description: {abstr['description']}"
            context += info_line + "\\n"
            abstraction_info_for_prompt.append(
                f"{i} # {abstr['name']}"
            )  # Use potentially translated name here too
            all_relevant_indices.update(abstr["files"])

        context += "\\nRelevant File Snippets (Referenced by Index and Path):\\n"
        # Get content for relevant files using helper
        relevant_files_content_map = get_content_for_indices(
            files_data, sorted(list(all_relevant_indices))
        )
        # Format file content for context
        file_context_str = "\\n\\n".join(
            f"--- File: {idx_path} ---\\n{content}"
            for idx_path, content in relevant_files_content_map.items()
        )
        context += file_context_str

        return (
            context,
            "\n".join(abstraction_info_for_prompt),
            num_abstractions,  # Pass the actual count
            project_name,
            language,
            use_cache,
        )  # Return use_cache

    def exec(self, prep_res):
        start_time = time.time()
        (
            context,
            abstraction_listing,
            num_abstractions,  # Receive the actual count
            project_name,
            language,
            use_cache,
        ) = prep_res  # Unpack use_cache

        print_operation("Analyzing relationships...", Icons.ANALYZING, indent=1)

        # Add language instruction and hints only if not English
        language_instruction = ""
        lang_hint = ""
        list_lang_note = ""
        if language.lower() != "english":
            language_instruction = f"IMPORTANT: Generate the `summary` and relationship `label` fields in **{language.capitalize()}** language. Do NOT use English for these fields.\n\n"
            lang_hint = f" (in {language.capitalize()})"
            list_lang_note = f" (Names might be in {language.capitalize()})"  # Note for the input list

        prompt = f"""
Based on the following abstractions and relevant code snippets from the project `{project_name}`:

List of Abstraction Indices and Names{list_lang_note}:
{abstraction_listing}

Context (Abstractions, Descriptions, Code):
{context}

{language_instruction}Please provide:
1. A high-level technical `summary` of the project's purpose, architecture, functionalities and their responsibilities{lang_hint}. Use markdown formatting with **bold** and *italic* text to highlight important concepts.
2. A list (`relationships`) describing the key interactions between these abstractions. For each relationship, specify:
    - `from_abstraction`: Index of the source abstraction (e.g., `0 # AbstractionName1`)
    - `to_abstraction`: Index of the target abstraction (e.g., `1 # AbstractionName2`)
    - `label`: A brief label for the interaction **in just a few words**{lang_hint} (e.g., "Manages", "Inherits", "Uses").
    Ideally the relationship should be backed by one abstraction calling or passing parameters to another.
    Simplify the relationship and exclude those non-important ones.

IMPORTANT: Make sure EVERY abstraction is involved in at least ONE relationship (either as source or target). Each abstraction index must appear at least once across all relationships.

Format the output as YAML:

```yaml
summary: |
  A technical overview of the project architecture{lang_hint}.
  Can span multiple lines with **bold** and *italic* for emphasis.
relationships:
  - from_abstraction: 0 # AbstractionName1
    to_abstraction: 1 # AbstractionName2
    label: "Manages"{lang_hint}
  - from_abstraction: 2 # AbstractionName3
    to_abstraction: 0 # AbstractionName1
    label: "Provides config"{lang_hint}
  # ... other relationships
```

Now, provide the YAML output:
"""
        response = call_llm(
            prompt, use_cache=(use_cache and self.cur_retry == 0)
        )  # Use cache only if enabled and not retrying

        # --- Validation ---
        yaml_str = response.strip().split("```yaml")[1].split("```")[0].strip()
        relationships_data = yaml.safe_load(yaml_str)

        if not isinstance(relationships_data, dict) or not all(
            k in relationships_data for k in ["summary", "relationships"]
        ):
            raise ValueError(
                "LLM output is not a dict or missing keys ('summary', 'relationships')"
            )
        if not isinstance(relationships_data["summary"], str):
            raise ValueError("summary is not a string")
        if not isinstance(relationships_data["relationships"], list):
            raise ValueError("relationships is not a list")

        # Validate relationships structure
        validated_relationships = []
        for rel in relationships_data["relationships"]:
            # Check for 'label' key
            if not isinstance(rel, dict) or not all(
                k in rel for k in ["from_abstraction", "to_abstraction", "label"]
            ):
                raise ValueError(
                    f"Missing keys (expected from_abstraction, to_abstraction, label) in relationship item: {rel}"
                )
            # Validate 'label' is a string
            if not isinstance(rel["label"], str):
                raise ValueError(f"Relationship label is not a string: {rel}")

            # Validate indices
            try:
                from_idx = int(str(rel["from_abstraction"]).split("#")[0].strip())
                to_idx = int(str(rel["to_abstraction"]).split("#")[0].strip())
                if not (
                    0 <= from_idx < num_abstractions and 0 <= to_idx < num_abstractions
                ):
                    raise ValueError(
                        f"Invalid index in relationship: from={from_idx}, to={to_idx}. Max index is {num_abstractions-1}."
                    )
                validated_relationships.append(
                    {
                        "from": from_idx,
                        "to": to_idx,
                        "label": rel["label"],  # Potentially translated label
                    }
                )
            except (ValueError, TypeError):
                raise ValueError(f"Could not parse indices from relationship: {rel}")

        elapsed = time.time() - start_time
        print_success("Generated project summary", elapsed, indent=2)

        return {
            "summary": relationships_data["summary"],  # Potentially translated summary
            "details": validated_relationships,  # Store validated, index-based relationships with potentially translated labels
        }

    def post(self, shared, prep_res, exec_res):
        # Structure is now {"summary": str, "details": [{"from": int, "to": int, "label": str}]}
        # Summary and label might be translated
        shared["relationships"] = exec_res


class OrderComponents(Node):
    def prep(self, shared):
        abstractions = shared["abstractions"]  # Name/description might be translated
        relationships = shared["relationships"]  # Summary/label might be translated
        project_name = shared["project_name"]  # Get project name
        language = shared.get("language", "english")  # Get language
        use_cache = shared.get("use_cache", True)  # Get use_cache flag, default to True

        # Prepare context for the LLM
        abstraction_info_for_prompt = []
        for i, a in enumerate(abstractions):
            abstraction_info_for_prompt.append(
                f"- {i} # {a['name']}"
            )  # Use potentially translated name
        abstraction_listing = "\n".join(abstraction_info_for_prompt)

        # Use potentially translated summary and labels
        summary_note = ""
        if language.lower() != "english":
            summary_note = (
                f" (Note: Project Summary might be in {language.capitalize()})"
            )

        context = f"Project Summary{summary_note}:\n{relationships['summary']}\n\n"
        context += "Relationships (Indices refer to abstractions above):\n"
        for rel in relationships["details"]:
            from_name = abstractions[rel["from"]]["name"]
            to_name = abstractions[rel["to"]]["name"]
            # Use potentially translated 'label'
            context += f"- From {rel['from']} ({from_name}) to {rel['to']} ({to_name}): {rel['label']}\n"  # Label might be translated

        list_lang_note = ""
        if language.lower() != "english":
            list_lang_note = f" (Names might be in {language.capitalize()})"

        return (
            abstraction_listing,
            context,
            len(abstractions),
            project_name,
            list_lang_note,
            use_cache,
        )  # Return use_cache

    def exec(self, prep_res):
        start_time = time.time()
        (
            abstraction_listing,
            context,
            num_abstractions,
            project_name,
            list_lang_note,
            use_cache,
        ) = prep_res  # Unpack use_cache

        print_operation("Determining component order...", Icons.ORDERING, indent=1)
        # No language variation needed here in prompt instructions, just ordering based on structure
        # The input names might be translated, hence the note.
        prompt = f"""
Given the following project abstractions and their relationships for the project ```` {project_name} ````:

Abstractions (Index # Name){list_lang_note}:
{abstraction_listing}

Context about relationships and project summary:
{context}

If you are going to create technical documentation for ```` {project_name} ````, what is the best order to document these components, from first to last?
Ideally, first document those that are the most important or foundational, perhaps user-facing concepts or entry points. Then move to more detailed, lower-level implementation details or supporting concepts.

Output the ordered list of abstraction indices, including the name in a comment for clarity. Use the format `idx # AbstractionName`.

```yaml
- 2 # FoundationalConcept
- 0 # CoreClassA
- 1 # CoreClassB (uses CoreClassA)
- ...
```

Now, provide the YAML output:
"""
        response = call_llm(
            prompt, use_cache=(use_cache and self.cur_retry == 0)
        )  # Use cache only if enabled and not retrying

        # --- Validation ---
        yaml_str = response.strip().split("```yaml")[1].split("```")[0].strip()
        ordered_indices_raw = yaml.safe_load(yaml_str)

        if not isinstance(ordered_indices_raw, list):
            raise ValueError("LLM output is not a list")

        ordered_indices = []
        seen_indices = set()
        for entry in ordered_indices_raw:
            try:
                if isinstance(entry, int):
                    idx = entry
                elif isinstance(entry, str) and "#" in entry:
                    idx = int(entry.split("#")[0].strip())
                else:
                    idx = int(str(entry).strip())

                if not (0 <= idx < num_abstractions):
                    raise ValueError(
                        f"Invalid index {idx} in ordered list. Max index is {num_abstractions-1}."
                    )
                if idx in seen_indices:
                    raise ValueError(f"Duplicate index {idx} found in ordered list.")
                ordered_indices.append(idx)
                seen_indices.add(idx)

            except (ValueError, TypeError):
                raise ValueError(
                    f"Could not parse index from ordered list entry: {entry}"
                )

        # Check if all abstractions are included
        if len(ordered_indices) != num_abstractions:
            raise ValueError(
                f"Ordered list length ({len(ordered_indices)}) does not match number of abstractions ({num_abstractions}). Missing indices: {set(range(num_abstractions)) - seen_indices}"
            )

        elapsed = time.time() - start_time
        print_success(f"Order determined: {ordered_indices}", elapsed, indent=2)
        print_phase_end()

        return ordered_indices  # Return the list of indices

    def post(self, shared, prep_res, exec_res):
        # exec_res is already the list of ordered indices
        shared["component_order"] = exec_res  # List of indices


class WriteComponents(BatchNode):
    def prep(self, shared):
        component_order = shared["component_order"]  # List of indices
        abstractions = shared[
            "abstractions"
        ]  # List of {"name": str, "description": str, "files": [int]}
        files_data = shared["files"]  # List of (path, content) tuples
        language = shared.get("language", "english")
        use_cache = shared.get("use_cache", True)  # Get use_cache flag, default to True
        documentation_mode = shared.get(
            "documentation_mode", "minimal"
        )  # Get documentation_mode, default to minimal

        # Get already written components to provide context
        # We store them temporarily during the batch run, not in shared memory yet
        # The 'previous_components_summary' will be built progressively in the exec context
        self.components_written_so_far = (
            []
        )  # Use instance variable for temporary storage across exec calls

        # Create a complete list of all components
        all_components = []
        component_filenames = {}  # Store component filename mapping for linking
        for i, abstraction_index in enumerate(component_order):
            if 0 <= abstraction_index < len(abstractions):
                component_num = i + 1
                component_name = abstractions[abstraction_index][
                    "name"
                ]  # Potentially translated name
                # Create safe filename (from potentially translated name)
                safe_name = "".join(
                    c if c.isalnum() else "_" for c in component_name
                ).lower()
                filename = f"{i+1:02d}_{safe_name}.md"
                # Format with link (using potentially translated name)
                # Strip newlines from component name to prevent broken markdown links
                clean_component_name = component_name.replace("\n", " ").strip()
                all_components.append(
                    f"{component_num}. [{clean_component_name}]({filename})"
                )
                # Store mapping of component index to filename for linking
                component_filenames[abstraction_index] = {
                    "num": component_num,
                    "name": component_name,
                    "filename": filename,
                }

        full_component_listing = "\n".join(all_components)

        items_to_process = []
        for i, abstraction_index in enumerate(component_order):
            if 0 <= abstraction_index < len(abstractions):
                abstraction_details = abstractions[
                    abstraction_index
                ]  # Contains potentially translated name/desc
                # Use 'files' (list of indices) directly
                related_file_indices = abstraction_details.get("files", [])
                # Get content using helper, passing indices
                related_files_content_map = get_content_for_indices(
                    files_data, related_file_indices
                )

                prev_component = None
                if i > 0:
                    prev_idx = component_order[i - 1]
                    prev_component = component_filenames[prev_idx]

                next_component = None
                if i < len(component_order) - 1:
                    next_idx = component_order[i + 1]
                    next_component = component_filenames[next_idx]

                items_to_process.append(
                    {
                        "component_num": i + 1,
                        "abstraction_index": abstraction_index,
                        "abstraction_details": abstraction_details,  # Has potentially translated name/desc
                        "related_files_content_map": related_files_content_map,
                        "project_name": shared["project_name"],  # Add project name
                        "full_component_listing": full_component_listing,
                        "component_filenames": component_filenames,
                        "prev_component": prev_component,
                        "next_component": next_component,
                        "language": language,
                        "use_cache": use_cache,
                        "documentation_mode": documentation_mode,
                    }
                )
            else:
                print(
                    f"Warning: Invalid abstraction index {abstraction_index} in component_order. Skipping."
                )

        print_phase_start("Content Generation", Icons.WRITING)
        return items_to_process  # Iterable for BatchNode

    def exec(self, item):
        start_time = time.time()
        # This runs for each item prepared above
        abstraction_name = item["abstraction_details"][
            "name"
        ]  # Potentially translated name
        abstraction_description = item["abstraction_details"][
            "description"
        ]  # Potentially translated description
        component_num = item["component_num"]
        project_name = item.get("project_name")
        language = item.get("language", "english")
        use_cache = item.get("use_cache", True)  # Read use_cache from item
        documentation_mode = item.get(
            "documentation_mode", "minimal"
        )  # Read documentation_mode from item

        # Prepare file context string from the map
        file_context_str = "\n\n".join(
            f"--- File: {idx_path.split('# ')[1] if '# ' in idx_path else idx_path} ---\n{content}"
            for idx_path, content in item["related_files_content_map"].items()
        )

        # Get summary of components written *before* this one
        # Use the temporary instance variable
        previous_components_summary = "\n---\n".join(self.components_written_so_far)

        # Add language instruction and context notes only if not English
        language_instruction = ""
        concept_details_note = ""
        structure_note = ""
        prev_summary_note = ""
        instruction_lang_note = ""
        mermaid_lang_note = ""
        code_comment_note = ""
        link_lang_note = ""
        tone_note = ""
        if language.lower() != "english":
            lang_cap = language.capitalize()
            language_instruction = f"IMPORTANT: Write this ENTIRE documentation component in **{lang_cap}**. Some input context (like concept name, description, component list, previous summary) might already be in {lang_cap}, but you MUST translate ALL other generated content including explanations, examples, technical terms, and potentially code comments into {lang_cap}. DO NOT use English anywhere except in code syntax, required proper nouns, or when specified. The entire output MUST be in {lang_cap}.\n\n"
            concept_details_note = f" (Note: Provided in {lang_cap})"
            structure_note = f" (Note: Component names might be in {lang_cap})"
            prev_summary_note = f" (Note: This summary might be in {lang_cap})"
            instruction_lang_note = f" (in {lang_cap})"
            mermaid_lang_note = f" (Use {lang_cap} for labels/text if appropriate)"
            code_comment_note = f" (Translate to {lang_cap} if possible, otherwise keep minimal English for clarity)"
            link_lang_note = (
                f" (Use the {lang_cap} component title from the structure above)"
            )
            tone_note = f" (appropriate for {lang_cap} readers)"

        # Build prompt based on mode
        if documentation_mode == "minimal":
            # Minimal mode: shorter, more direct instructions
            prompt = f"""
{language_instruction}Write short and concise intent-focused documentation. Be brief but keep all critical info: architecture, design, components, integrations. Focus on key facts and intent. Avoid verbosity. Keep structure but be direct.

Write technical documentation (in Markdown format) for engineers working with the component "{abstraction_name}" in the project `{project_name}`. This is Component {component_num}.

Component/Concept Details{concept_details_note}:
- Name: {abstraction_name}
- Description:
{abstraction_description}

Complete Documentation Structure{structure_note}:
{item["full_component_listing"]}

Context from previous components{prev_summary_note}:
{previous_components_summary if previous_components_summary else "This is the first component."}

Relevant Code Snippets (Code itself remains unchanged):
{file_context_str if file_context_str else "No specific code snippets provided for this abstraction."}

Instructions for the documentation (Generate content in {language.capitalize()} unless specified otherwise):
- Start with clear heading: `# Component {component_num}: {abstraction_name}`. Use the provided component name.

- If not first component, reference previous component{instruction_lang_note} with Markdown link{link_lang_note}.

- Why it exists{instruction_lang_note}: core responsibilities, purpose in architecture.

- What it does{instruction_lang_note}: key responsibilities, how it works, integration points.

- Avoid code blocks if not critical. If code blocks are needed, keep them BELOW 5 lines. Simplify aggressively. Use comments{code_comment_note} to skip non-essential details. Explain after each block{instruction_lang_note}. No imports/packages.

- Internal implementation{instruction_lang_note}: step-by-step walkthrough (code-light). Use simple sequenceDiagram (max 5 participants). If participant name has space: `participant QP as Query Processing`. {mermaid_lang_note}.

- IMPORTANT: Link to other components: [Component Title](filename.md). Use Complete Documentation Structure for filename/title{link_lang_note}.

- Use mermaid diagrams for complex concepts (```mermaid``` format). {mermaid_lang_note}.

- Key takeaways{instruction_lang_note}: what it handles, common patterns, integration points. Link to next component if exists{link_lang_note}.

- Tone: technical and precise{tone_note}.

- Output *only* Markdown content (DONT NEED ```markdown``` tags).
"""
        else:
            # Comprehensive mode: ORIGINAL prompt unchanged
            prompt = f"""
{language_instruction}Write technical documentation (in Markdown format) for engineers working with the component "{abstraction_name}" in the project `{project_name}`. This is Component {component_num}.

Component/Concept Details{concept_details_note}:
- Name: {abstraction_name}
- Description:
{abstraction_description}

Complete Documentation Structure{structure_note}:
{item["full_component_listing"]}

Context from previous components{prev_summary_note}:
{previous_components_summary if previous_components_summary else "This is the first component."}

Relevant Code Snippets (Code itself remains unchanged):
{file_context_str if file_context_str else "No specific code snippets provided for this abstraction."}

Instructions for the documentation (Generate content in {language.capitalize()} unless specified otherwise):
- Start with a clear heading (e.g., `# Component {component_num}: {abstraction_name}`). Use the provided component name.

- If this is not the first component, begin with a brief reference to the previous component{instruction_lang_note}, linking to it with a proper Markdown link using its name{link_lang_note}.

- Begin with why this component exists{instruction_lang_note} - what problem it solves and its core responsibilities. Focus on the component's purpose in the system architecture.

- Document what this component does{instruction_lang_note} - its key responsibilities, how it works, and how it integrates with other components.

- If the component is complex, break it down into key concepts. Explain each concept with technical precision{instruction_lang_note}.

- Each code block should be BELOW 10 lines! If longer code blocks are needed, break them down into smaller pieces and walk through them one-by-one. Aggresively simplify the code to make it minimal. Use comments{code_comment_note} to skip non-important implementation details. Each code block should have a solid explanation right after it{instruction_lang_note}. Make sure you dont include Imports or packages in the code blocks, keep it focused on the key logic always.

- Describe the internal implementation to help understand what's under the hood{instruction_lang_note}. First provide a non-code or code-light walkthrough on what happens step-by-step when the abstraction is called{instruction_lang_note}. It's recommended to use a simple sequenceDiagram - keep it minimal with at most 5 participants to ensure clarity. If participant name has space, use: `participant QP as Query Processing`. {mermaid_lang_note}.

- Then dive deeper into code for the internal implementation with references to files. Provide example code blocks, but make them similarly simple and beginner-friendly. Dont include imports or packages in the code blocks. Explain{instruction_lang_note}.

- IMPORTANT: When you need to refer to other core components covered in other sections, ALWAYS use proper Markdown links like this: [Component Title](filename.md). Use the Complete Documentation Structure above to find the correct filename and the component title{link_lang_note}. Translate the surrounding text.

- Use mermaid diagrams to illustrate complex concepts (```mermaid``` format). {mermaid_lang_note}.

- Provide concrete code examples from the codebase showing actual usage and implementation patterns{instruction_lang_note}.

- End the component documentation with key takeaways{instruction_lang_note}: what this component handles, common usage patterns, and integration points. If there is a next component, use a proper Markdown link: [Next Component Title](next_component_filename){link_lang_note}.

- Ensure the tone is technical and precise{tone_note}.

- Output *only* the Markdown content for this component.

Now, directly provide technical Markdown documentation (DON'T need ```markdown``` tags):
"""
        component_content = call_llm(
            prompt, use_cache=(use_cache and self.cur_retry == 0)
        )  # Use cache only if enabled and not retrying

        elapsed = time.time() - start_time

        # Store timing for later summary
        if not hasattr(self, "component_times"):
            self.component_times = []
        self.component_times.append(elapsed)

        # Show the operation with timing
        print_operation(
            f"Component {component_num}: {abstraction_name}",
            Icons.WRITING,
            indent=1,
            elapsed_time=elapsed,
        )
        # Basic validation/cleanup
        actual_heading = f"# Component {component_num}: {abstraction_name}"  # Use potentially translated name
        if not component_content.strip().startswith(f"# Component {component_num}"):
            # Add heading if missing or incorrect, trying to preserve content
            lines = component_content.strip().split("\n")
            if lines and lines[0].strip().startswith(
                "#"
            ):  # If there's some heading, replace it
                lines[0] = actual_heading
                component_content = "\n".join(lines)
            else:  # Otherwise, prepend it
                component_content = f"{actual_heading}\n\n{component_content}"

        # Add the generated content to our temporary list for the next iteration's context
        self.components_written_so_far.append(component_content)

        return component_content  # Return the Markdown string (potentially translated)

    def post(self, shared, prep_res, exec_res_list):
        # exec_res_list contains the generated Markdown for each component, in order
        shared["components"] = exec_res_list

        # Calculate total time
        total_time = (
            sum(self.component_times) if hasattr(self, "component_times") else 0
        )
        print_success(f"{len(exec_res_list)} components written", total_time, indent=1)
        print_phase_end()

        # Cleanup
        if hasattr(self, "component_times"):
            del self.component_times
        if hasattr(self, "components_written_so_far"):
            del self.components_written_so_far


class GenerateDocContent(Node):
    def prep(self, shared):
        project_name = shared["project_name"]
        output_base_dir = shared.get("output_dir", "output")  # Default output dir
        output_path = output_base_dir
        repo_url = shared.get("repo_url")  # Get the repository URL

        # Get potentially translated data
        relationships_data = shared[
            "relationships"
        ]  # {"summary": str, "details": [{"from": int, "to": int, "label": str}]} -> summary/label potentially translated
        component_order = shared["component_order"]  # indices
        abstractions = shared[
            "abstractions"
        ]  # list of dicts -> name/description potentially translated
        components_content = shared[
            "components"
        ]  # list of strings -> content potentially translated

        return {
            "project_name": project_name,
            "output_path": output_path,
            "repo_url": repo_url,
            "relationships_data": relationships_data,
            "component_order": component_order,
            "abstractions": abstractions,
            "components_content": components_content,
        }

    def _generate_combined_content(
        self, project_name, index_content, components_content
    ):
        """Generate the combined documentation file content."""
        from wikigen.utils.adjust_headings import (
            adjust_heading_levels,
            strip_attribution_footer,
        )

        # Start with H1 repo name
        combined = f"# {project_name}\n\n"

        # Add index content without attribution footer
        index_without_attribution = strip_attribution_footer(index_content)
        combined += index_without_attribution

        # Add separator
        combined += "\n\n---\n\n"

        # Add each component with headings shifted down one level
        for i, component_content in enumerate(components_content):
            adjusted_component = adjust_heading_levels(component_content, shift=1)
            combined += adjusted_component

            # Add separator between components (except for the last one)
            if i < len(components_content) - 1:
                combined += "\n\n---\n\n"

        # Add separator at the bottom
        combined += (
            "\n\n---\n\nWiki created by [WIKIGEN](https://github.com/usesalt/wikigen)\n"
        )

        return combined

    def exec(self, prep_res):
        start_time = time.time()
        project_name = prep_res["project_name"]
        output_path = prep_res["output_path"]
        repo_url = prep_res["repo_url"]
        relationships_data = prep_res["relationships_data"]
        component_order = prep_res["component_order"]
        abstractions = prep_res["abstractions"]
        components_content = prep_res["components_content"]

        print_phase_start("Documentation Assembly", Icons.GENERATING)

        # --- Generate Mermaid Diagram ---
        mermaid_lines = ["flowchart TD"]
        # Add nodes for each abstraction using potentially translated names
        for i, abstr in enumerate(abstractions):
            node_id = f"A{i}"
            # Use potentially translated name, sanitize for Mermaid ID and label
            # Remove quotes and line breaks to avoid Mermaid syntax issues
            sanitized_name = abstr["name"].replace('"', "").replace("\n", " ").strip()
            node_label = sanitized_name
            mermaid_lines.append(
                f'    {node_id}["{node_label}"]'
            )  # Node label uses potentially translated name
        # Add edges for relationships using potentially translated labels
        for rel in relationships_data["details"]:
            from_node_id = f"A{rel['from']}"
            to_node_id = f"A{rel['to']}"
            # Use potentially translated label, sanitize
            edge_label = (
                rel["label"].replace('"', "").replace("\n", " ")
            )  # Basic sanitization
            max_label_len = 30
            if len(edge_label) > max_label_len:
                edge_label = edge_label[: max_label_len - 3] + "..."
            mermaid_lines.append(
                f'    {from_node_id} -- "{edge_label}" --> {to_node_id}'
            )  # Edge label uses potentially translated label

        mermaid_diagram = "\n".join(mermaid_lines)
        # --- End Mermaid ---

        # --- Prepare index.md content ---
        index_content = f"{relationships_data['summary']}\n\n"  # Use the potentially translated summary directly
        # Keep fixed strings in English
        index_content += f"**Source Repository:** [{repo_url}]({repo_url})\n\n"

        # Add Mermaid diagram for relationships (diagram itself uses potentially translated names/labels)
        index_content += "```mermaid\n"
        index_content += mermaid_diagram + "\n"
        index_content += "```\n\n"

        # Keep fixed strings in English
        index_content += "## Components\n\n"

        component_files = []
        # Generate component links based on the determined order, using potentially translated names
        for i, abstraction_index in enumerate(component_order):
            # Ensure index is valid and we have content for it
            if 0 <= abstraction_index < len(abstractions) and i < len(
                components_content
            ):
                abstraction_name = abstractions[abstraction_index][
                    "name"
                ]  # Potentially translated name
                # Sanitize potentially translated name for filename
                safe_name = "".join(
                    c if c.isalnum() else "_" for c in abstraction_name
                ).lower()
                filename = f"{i+1:02d}_{safe_name}.md"
                # Strip newlines from component name to prevent broken markdown links
                clean_abstraction_name = abstraction_name.replace("\n", " ").strip()
                index_content += f"{i+1}. [{clean_abstraction_name}]({filename})\n"  # Use potentially translated name in link text

                # Component content without attribution footer
                component_content = components_content[
                    i
                ]  # Potentially translated content

                # Store filename and corresponding content
                component_files.append(
                    {"filename": filename, "content": component_content}
                )
            else:
                print(
                    f"Warning: Mismatch between component order, abstractions, or content at index {i} (abstraction index {abstraction_index}). Skipping file generation for this entry."
                )

        # Add attribution to index content (using English fixed string)
        index_content += "\n\n---\n\nGenerated by [WIKIGEN](https://usesalt.co)"

        # Generate combined content
        combined_content = self._generate_combined_content(
            project_name, index_content, components_content
        )

        elapsed = time.time() - start_time
        print_success("Generated index and combined files", elapsed, indent=1)
        print_phase_end()

        return {
            "project_name": project_name,
            "output_path": output_path,
            "index_content": index_content,
            "component_files": component_files,
            "combined_content": combined_content,
        }

    def post(self, shared, prep_res, exec_res):
        shared["doc_content"] = exec_res  # Store the content dict


class WriteDocFiles(Node):
    def prep(self, shared):
        return shared["doc_content"]

    def exec(self, doc_content):
        start_time = time.time()
        project_name = doc_content["project_name"]
        output_path = doc_content["output_path"]
        combined_content = doc_content["combined_content"]

        print_phase_start("Writing Output Files", Icons.CREATING)
        # Rely on Node's built-in retry/fallback
        os.makedirs(output_path, exist_ok=True)

        # Write combined file
        combined_filepath = os.path.join(output_path, f"{project_name}.md")
        with open(combined_filepath, "w", encoding="utf-8") as f:
            f.write(combined_content)
        print_operation(f"{Icons.SUCCESS} {project_name}.md", indent=1)

        elapsed = time.time() - start_time
        print_success("Documentation file written", elapsed, indent=1)

        return output_path  # Return the final path

    def post(self, shared, prep_res, exec_res):
        shared["final_output_dir"] = exec_res  # Store the output path
