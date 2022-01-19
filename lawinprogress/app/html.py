"""MVP of the LiP Webapp."""
from anytree import PreOrderIter
from fastapi import FastAPI, Form, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates

from lawinprogress.generate_diff import parse_and_apply_changes, process_pdf
from lawinprogress.libdiff.html_diff import html_diffs

app = FastAPI()
templates = Jinja2Templates(directory="lawinprogress/app/templates/")


@app.get("/")
def upload_pdf(request: Request):
    """Get the upload form page."""
    result = "Upload a change law pdf."
    return templates.TemplateResponse(
        "upload_form.html", context={"request": request, "result": result}
    )


@app.post("/")
def generate_diff(request: Request, change_law_pdf: UploadFile = Form(...)):
    """
    Submit the upload form with the pdf path and process it.

    Return the result.
    """
    law_titles, proposals_list = process_pdf(change_law_pdf.file)

    results = []
    for law_title, change_law_text in zip(law_titles, proposals_list):
        # find and load the source law
        source_law_path = f"data/source_laws/{law_title}.txt"
        try:
            with open(source_law_path, "r", encoding="utf8") as file:
                source_law_text = file.read()
        except FileNotFoundError as err:
            results.append("<p>Source law not found.</p>")
            continue

        # Parse the source and change law and apply the requested changes.
        (
            parsed_law_tree,
            res_law_tree,
            change_requests,
            change_results,
            n_succesfull_applied_changes,
        ) = parse_and_apply_changes(
            change_law_text, source_law_text, law_title, loglevel=2
        )

        # generate the html diff
        applied_change_results = [
            node.changes for node in PreOrderIter(res_law_tree) if node.changes
        ]
        # get the diff
        html_side_by_side = html_diffs(
            parsed_law_tree.to_text(),
            res_law_tree.to_text(),
            applied_change_results,
        )
        results.append(html_side_by_side)

    # prepare the html output and return it
    result = list(zip(law_titles, results))
    return templates.TemplateResponse(
        "results_index.html",
        context={"request": request, "result": result, "name": change_law_pdf.filename},
    )


@app.get("/imgs/{image_name}")
def get_image_resource(image_name: str):
    """Fetch image resource from server."""
    return FileResponse(f"lawinprogress/app/templates/imgs/{image_name}")
