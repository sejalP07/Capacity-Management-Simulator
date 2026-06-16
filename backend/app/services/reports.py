from __future__ import annotations

import csv
import io
import json

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.models import Simulation


def json_report(simulation: Simulation) -> bytes:
    return json.dumps(
        {
            "id": simulation.id,
            "cluster_id": simulation.cluster_id,
            "algorithm": simulation.algorithm,
            "traffic_pattern": simulation.traffic_pattern,
            "duration_hours": simulation.duration_hours,
            "results": simulation.results,
        },
        indent=2,
    ).encode("utf-8")


def csv_report(simulation: Simulation) -> bytes:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["timestamp", "cpu", "memory", "storage", "traffic_multiplier"])
    writer.writeheader()
    for point in simulation.results.get("timeline", []):
        writer.writerow(point)
    return output.getvalue().encode("utf-8")


def pdf_report(simulation: Simulation) -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 72

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(72, y, "Capacity Management Simulation Report")
    y -= 32
    pdf.setFont("Helvetica", 10)
    lines = [
        f"Simulation ID: {simulation.id}",
        f"Cluster ID: {simulation.cluster_id}",
        f"Algorithm: {simulation.algorithm}",
        f"Traffic Pattern: {simulation.traffic_pattern}",
        f"Duration: {simulation.duration_hours} hours",
    ]
    for line in lines:
        pdf.drawString(72, y, line)
        y -= 18

    y -= 12
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(72, y, "Peak Utilization")
    y -= 20
    pdf.setFont("Helvetica", 10)
    for resource, value in simulation.results.get("peak_utilization", {}).items():
        pdf.drawString(72, y, f"{resource.upper()}: {value}%")
        y -= 16

    y -= 10
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(72, y, "Bottlenecks")
    y -= 20
    pdf.setFont("Helvetica", 10)
    for finding in simulation.results.get("bottlenecks", []):
        pdf.drawString(72, y, f"- {finding}")
        y -= 16
        if y < 80:
            pdf.showPage()
            y = height - 72

    pdf.save()
    return buffer.getvalue()
