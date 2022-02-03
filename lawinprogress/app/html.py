"""LiP Webapp."""
import logging
import os
import random
import string
import time

from anytree import PreOrderIter
from fastapi import FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates

from lawinprogress.generate_diff import (
    parse_and_apply_changes,
    process_pdf,
    retrieve_source_law,
)
from lawinprogress.libdiff.html_diff import html_diffs

# setup loggers
logging.config.fileConfig("logging.conf", disable_existing_loggers=True)
logger = logging.getLogger(__name__)


app = FastAPI()
templates = Jinja2Templates(directory="lawinprogress/templates/")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log runtime of requests with a unique id."""
    idem = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    logger.info(f"rid={idem} start request path={request.url.path}")
    start_time = time.time()

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    formatted_process_time = "{0:.2f}".format(process_time)
    logger.info(
        f"rid={idem} completed_in={formatted_process_time}ms status_code={response.status_code}"
    )

    return response


@app.get("/")
async def upload_pdf(request: Request):
    """Get the upload form page."""
    result = "Lade einen Entwurf eines Änderungsgesetztes hoch:"
    return templates.TemplateResponse(
        "upload_form.html", context={"request": request, "result": result}
    )


@app.post("/")
def generate_diff(request: Request, change_law_pdf: UploadFile = Form(...)):
    """
    Submit the upload form with the pdf path and process it.

    Return the result.
    """
    try:
        law_titles, proposals_list = process_pdf(change_law_pdf.file)
        logger.info(f"Processing {change_law_pdf.filename}...")

        results = []
        for law_title, change_law_text in zip(law_titles, proposals_list):
            logger.info(f"Started processing change for {law_title}...")
            # find and load the source law
            source_law = retrieve_source_law(law_title)
            if not source_law:
                results.append("<p>Source law not found.</p>")

            # Parse the source and change law and apply the requested changes.
            (
                parsed_law_tree,
                res_law_tree,
                change_requests,
                change_results,
                n_succesfull_applied_changes,
            ) = parse_and_apply_changes(
                change_law_text,
                source_law,
                law_title,
            )

            # generate the html diff
            applied_change_results = [
                node.changes
                for node in PreOrderIter(
                    res_law_tree, filter_=lambda node: node.bulletpoint != "source"
                )
                if node.changes
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
            context={
                "request": request,
                "result": result,
                "name": change_law_pdf.filename,
            },
        )
    except Exception as err:
        logger.info(err)
        return templates.TemplateResponse(
            "errorpage.html",
            context={"request": request},
        )


@app.get("/imgs/{image_name}")
async def get_image_resource(request: Request, image_name: str):
    """Fetch image resource from server."""
    file_path = f"lawinprogress/templates/imgs/{image_name}"
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    else:
        logger.info("Requested file not found.")
        raise HTTPException(status_code=404, detail="Requested file not found")


@app.get("/css/{sheet}")
async def get_css_resource(sheet: str):
    """Fetch css stylesheet resource from server."""
    file_path = f"lawinprogress/templates/css/{sheet}"
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    else:
        logger.info("Requested file not found.")
        raise HTTPException(status_code=404, detail="Requested file not found")
