from flask import Flask, render_template, request, make_response, send_file, session, redirect, url_for, flash
from weasyprint import HTML, CSS
from docx import Document
import io
import os

# ==============================
# App Config
# ==============================
app = Flask(__name__)
app.secret_key = "your_secret_key"

# ==============================
# Resume storage (in-memory)
# ==============================
user_resume_data = {}

# ==============================
# Routes
# ==============================

@app.route('/')
def form():
    return render_template('form.html')


@app.route('/submit', methods=['POST'])
def submit():
    # Education
    educations = [
        (edu, uni)
        for edu, uni in zip(
            request.form.getlist('education[]'),
            request.form.getlist('university[]')
        )
        if edu.strip() or uni.strip()
    ]

    # Experience
    experiences = []
    jobs = request.form.getlist('job[]')
    companies = request.form.getlist('company[]')
    starts = request.form.getlist('start[]')
    ends = request.form.getlist('end[]')
    descs = request.form.getlist('desc[]')
    continued_flags = request.form.getlist('continued[]')

    for i, job in enumerate(jobs):
        if not job.strip():
            continue

        company = companies[i] if i < len(companies) else ""
        start = starts[i] if i < len(starts) else ""
        end = ends[i] if i < len(ends) else ""
        desc = descs[i] if i < len(descs) else ""
        is_continued = continued_flags[i] == 'on' if i < len(continued_flags) else False

        period = f"{start} to Present" if is_continued else f"{start} to {end}"

        experiences.append({
            'job': job,
            'company': company,
            'period': period,
            'desc': desc
        })

    # Projects
    projects = [
        (title, detail)
        for title, detail in zip(
            request.form.getlist('project_title[]'),
            request.form.getlist('project_detail[]')
        )
        if title.strip() or detail.strip()
    ]

    # Skills
    skills = [s for s in request.form.getlist('skills[]') if s.strip()]

    global user_resume_data
    user_resume_data = {
        'name': request.form.get('name', ''),
        'address': request.form.get('address', ''),
        'phone': request.form.get('phone', ''),
        'email': request.form.get('email', ''),
        'educations': educations,
        'experiences': experiences,
        'projects': projects,
        'skills': skills
    }

    session['user_name'] = user_resume_data['name']

    return render_template('resume.html', **user_resume_data)


# ==============================
# Download DOCX
# ==============================

@app.route('/download_docx')
def download_docx():
    global user_resume_data

    if not user_resume_data:
        flash("Please generate your resume first.")
        return redirect(url_for('form'))

    doc = Document()

    # Header
    doc.add_heading(user_resume_data.get('name', ''), 0)
    doc.add_paragraph(
        f"{user_resume_data.get('address', '')} | "
        f"{user_resume_data.get('phone', '')} | "
        f"{user_resume_data.get('email', '')}"
    )

    # Education
    doc.add_heading('Education', level=1)
    for edu, uni in user_resume_data.get('educations', []):
        doc.add_paragraph(f"{edu} – {uni}")

    # Experience
    doc.add_heading('Experience', level=1)
    for exp in user_resume_data.get('experiences', []):
        p = doc.add_paragraph()
        p.add_run(f"{exp['job']} – {exp['company']}").bold = True
        p.add_run(f" ({exp['period']})")
        for line in exp['desc'].splitlines():
            doc.add_paragraph(line, style='ListBullet')

    # Projects
    doc.add_heading('Projects', level=1)
    for title, detail in user_resume_data.get('projects', []):
        doc.add_paragraph(f"{title}: {detail}")

    # Skills
    doc.add_heading('Technical Skills', level=1)
    doc.add_paragraph(', '.join(user_resume_data.get('skills', [])))

    file_stream = io.BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)

    return send_file(
        file_stream,
        as_attachment=True,
        download_name='resume.docx',
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )


# ==============================
# Download PDF
# ==============================

@app.route('/download_pdf')
def download_pdf():
    global user_resume_data

    if not user_resume_data:
        flash("Please generate your resume first.")
        return redirect(url_for('form'))

    rendered_html = render_template('resume.html', **user_resume_data)
    css_path = os.path.join('static', 'main.css')

    pdf = HTML(
        string=rendered_html,
        base_url=request.root_path
    ).write_pdf(
        stylesheets=[CSS(css_path)]
    )

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=resume.pdf'
    return response


# ==============================
# Run App
# ==============================

if __name__ == '__main__':
    app.run(debug=True)
