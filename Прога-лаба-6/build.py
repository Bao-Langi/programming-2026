from pathlib import Path
import yaml
from jinja2 import Environment, FileSystemLoader
import shutil

with open("data/questions.yaml", encoding="utf-8") as f:
    data = yaml.safe_load(f)

env = Environment(loader=FileSystemLoader("tempHTML"))
template = env.get_template("index.html")
html = template.render(**data)

Path("docs").mkdir(exist_ok=True)
Path("docs/index.html").write_text(html, encoding="utf-8")

shutil.copytree("gifs", "docs/gifs", dirs_exist_ok=True)
shutil.copy("static/style.css", "docs/style.css")
shutil.copy("static/script.js", "docs/script.js")