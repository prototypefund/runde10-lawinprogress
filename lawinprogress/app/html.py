"""LiP Webapp."""
import logging
import os
import random
import string
import time

from anytree import PreOrderIter
from fastapi import FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from lawinprogress.apply_changes.apply_changes import apply_changes
from lawinprogress.libdiff.html_diff import html_diffs
from lawinprogress.parsing.parse_change_law import parse_changes
from lawinprogress.parsing.parse_source_law import parse_source_law
from lawinprogress.processing.proposal_pdf_to_artikles import process_pdf
from lawinprogress.processing.source_law_retrieval import retrieve_source_law

# setup loggers
logging.config.fileConfig("logging.conf", disable_existing_loggers=True)
logger = logging.getLogger(__name__)


app = FastAPI()

app.mount("/imgs", StaticFiles(directory="lawinprogress/templates/imgs"), name="imgs")
app.mount("/css", StaticFiles(directory="lawinprogress/templates/css"), name="css")

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
        law_titles, proposals_list, full_law_title = process_pdf(change_law_pdf.file)
        logger.info(f"Processing {change_law_pdf.filename}...")

        results, n_changes, n_success = [], [], []
        for law_idx, (law_title, change_law_text) in enumerate(
            zip(law_titles, proposals_list)
        ):
            logger.info(f"Started processing change for {law_title}...")
            # find and load the source law
            source_law = retrieve_source_law(law_title)
            if not source_law:
                results.append("<p></p><p>Source law not found.</p><p></p>")

            # Parse the source and change law and apply the requested changes.
            # parse source law
            parsed_law_tree = parse_source_law(source_law, law_title=law_title)

            # parse changes
            change_requests = parse_changes(change_law_text, law_title)

            # apply changes to the source law
            res_law_tree, change_results, n_succesfull_applied_changes = apply_changes(
                parsed_law_tree,
                change_requests,
            )

            # generate the html diff
            applied_change_results = [
                node.changes
                for node in PreOrderIter(
                    res_law_tree,
                )
                if node.changes
            ]
            # get the diff
            html_side_by_side = html_diffs(
                parsed_law_tree.to_text(),
                res_law_tree.to_text(),
                applied_change_results,
                title=f"{law_idx+1}. {law_title}",
            )
            results.append(html_side_by_side)
            n_changes.append(len(change_requests))
            n_success.append(n_succesfull_applied_changes)

        # prepare the html output and return it
        law_titles = [f"{idx+1}. {title}" for idx, title in enumerate(law_titles)]
        result = list(zip(law_titles, n_changes, n_success, results))
        return templates.TemplateResponse(
            "results_index.html",
            context={
                "request": request,
                "result": result,
                "full_title": full_law_title,
                "name": change_law_pdf.filename,
            },
        )
    except Exception as err:
        logger.info(err)
        return templates.TemplateResponse(
            "errorpage.html",
            context={"request": request},
        )
