import re

with open('ermi/api.py', 'r') as f:
    content = f.read()

# Add validation to other endpoints
content = content.replace(
    '''    @app.post("/api/export/chatgpt-csv")
    def export_chatgpt_csv_endpoint(request: ExportRequest) -> dict[str, object]:
        source = Path(request.source).expanduser().resolve()
        target = (
            Path(request.target).expanduser().resolve()
            if request.target
            else root / "exports" / "chat_history.csv"
        )
        try:''',
    '''    @app.post("/api/export/chatgpt-csv")
    def export_chatgpt_csv_endpoint(request: ExportRequest) -> dict[str, object]:
        source = Path(request.source).expanduser().resolve()
        target = (
            Path(request.target).expanduser().resolve()
            if request.target
            else root / "exports" / "chat_history.csv"
        )
        validate_allowed_path(source, root)
        validate_allowed_path(target, root)
        try:'''
)

content = content.replace(
    '''    @app.post("/api/export/chatgpt-code")
    def export_chatgpt_code_endpoint(request: ExportRequest) -> dict[str, object]:
        source = Path(request.source).expanduser().resolve()
        target = (
            Path(request.target).expanduser().resolve()
            if request.target
            else root / "exports" / "all_extracted_code.txt"
        )
        try:''',
    '''    @app.post("/api/export/chatgpt-code")
    def export_chatgpt_code_endpoint(request: ExportRequest) -> dict[str, object]:
        source = Path(request.source).expanduser().resolve()
        target = (
            Path(request.target).expanduser().resolve()
            if request.target
            else root / "exports" / "all_extracted_code.txt"
        )
        validate_allowed_path(source, root)
        validate_allowed_path(target, root)
        try:'''
)

content = content.replace(
    '''    @app.post("/api/export/chatgpt-obsidian")
    def export_chatgpt_obsidian_endpoint(request: ExportRequest) -> dict[str, object]:
        source = Path(request.source).expanduser().resolve()
        target = (
            Path(request.target).expanduser().resolve()
            if request.target
            else root / "exports" / "chatgpt_obsidian"
        )
        try:''',
    '''    @app.post("/api/export/chatgpt-obsidian")
    def export_chatgpt_obsidian_endpoint(request: ExportRequest) -> dict[str, object]:
        source = Path(request.source).expanduser().resolve()
        target = (
            Path(request.target).expanduser().resolve()
            if request.target
            else root / "exports" / "chatgpt_obsidian"
        )
        validate_allowed_path(source, root)
        validate_allowed_path(target, root)
        try:'''
)

content = content.replace(
    '''    @app.get("/api/export/chatgpt-titles")
    def export_chatgpt_titles(source: str) -> dict[str, object]:
        try:
            titles = list_chat_titles(Path(source).expanduser().resolve())''',
    '''    @app.get("/api/export/chatgpt-titles")
    def export_chatgpt_titles(source: str) -> dict[str, object]:
        source_path = Path(source).expanduser().resolve()
        validate_allowed_path(source_path, root)
        try:
            titles = list_chat_titles(source_path)'''
)

content = content.replace(
    '''    @app.get("/api/export/chatgpt-activity")
    def export_chatgpt_activity(
        source: str, limit: Annotated[int, Query(ge=1, le=50)] = 5
    ) -> dict[str, object]:
        try:
            return {
                "activity": activity_summary(Path(source).expanduser().resolve(), limit)
            }''',
    '''    @app.get("/api/export/chatgpt-activity")
    def export_chatgpt_activity(
        source: str, limit: Annotated[int, Query(ge=1, le=50)] = 5
    ) -> dict[str, object]:
        source_path = Path(source).expanduser().resolve()
        validate_allowed_path(source_path, root)
        try:
            return {
                "activity": activity_summary(source_path, limit)
            }'''
)

content = content.replace(
    '''    @app.post("/api/restore")
    def restore(request: RestoreRequest) -> dict[str, object]:
        source = Path(request.source).expanduser().resolve()
        try:''',
    '''    @app.post("/api/restore")
    def restore(request: RestoreRequest) -> dict[str, object]:
        source = Path(request.source).expanduser().resolve()
        validate_allowed_path(source, root)
        try:'''
)

with open('ermi/api.py', 'w') as f:
    f.write(content)
