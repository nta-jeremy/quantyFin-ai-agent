# Task Planning and Summary Workflows

This document outlines the standardized workflow for creating task plans and summaries in the AI Performance Agent project.

## Summary Creation Workflow

### When to Create Summaries

Create summary files when:
- A planned task or feature has been completed
- A significant milestone has been reached
- A plan needs to be documented for future reference
- Post-completion analysis is required

### Summary File Management

**Location:** `/Users/tunganh252/Desktop/Study/AI101/quantyFin-ai-agent/vibeops/summaries/`

**Folder Structure:** Create date-based folders (YYYY-MM-DD format) and place summary files inside them.

**Naming Convention:** 
- **Folders:** `YYYY-MM-DD` (e.g., `2025-09-16`)
- **Summary Files:** `name-of-task-or-feature-summaries.md`

Examples:
- `2025-09-16/user-authentication-implementation-summaries.md`
- `2025-09-16/database-optimization-summaries.md`
- `2025-09-16/api-endpoint-refactor-summaries.md`

**Folder Creation Logic:**
- If a folder for today's date already exists, create the summary file in that existing folder
- If no folder exists for today's date, create a new date folder first, then create the summary file inside it

### Required Summary File Structure

Every summary file should include:

```markdown
# Summary: [Task/Feature Name]
**Status:** [Completed/Partially Completed/Cancelled]
**Owner:** [Responsible Person/Team]
**Date Completed:** [YYYY-MM-DD HH:MM:SS]
**Original Plan:** [Link to corresponding plan file]
**Actual Duration:** [Time taken]

## Full Summary
[Full summary]
```

## Best Practices

1. **Consistent Naming:** Always use the YYYY-MM-DD date format for folder names and clear, descriptive names for summary files
2. **Date-based Organization:** Create date folders for each day and place all summaries from that day inside the corresponding folder
3. **Descriptive Names:** Use clear, descriptive names that make the file's purpose obvious
4. **Link Plans to Summaries:** If there is a plan file, reference the original plan file in the summary
5. **Regular Updates:** Update plan files as work progresses
6. **Complete Documentation:** Ensure all required sections are filled out thoroughly
7. **File Organization:** Keep plans and summaries in their respective directories for easy navigation

## Directory Structure

```
vibeops/
├── summaries/
    ├── 2025-09-16/
    │   ├── feature-a-summaries.md
    │   ├── database-optimization-summaries.md
    │   └── api-refactor-summaries.md
    ├── 2025-09-17/
    │   ├── user-auth-summaries.md
    │   └── testing-implementation-summaries.md
    └── 2025-09-18/
        └── performance-optimization-summaries.md
```

This workflow ensures consistent documentation, easy tracking of task progress, and comprehensive project history for future reference.
