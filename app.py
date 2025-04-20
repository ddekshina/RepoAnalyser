# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import os
import threading
from main import GitHubRepoAnalyzer
import uuid
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_for_flash_messages')

# Directory for storing analysis reports
REPORTS_DIR = os.path.join(os.getcwd(), 'reports')
os.makedirs(REPORTS_DIR, exist_ok=True)

# Store analysis jobs
analysis_jobs = {}

def analyze_repo_async(job_id, repo_url, api_key, output_type, generate_pdf=False):
    """Run the repository analysis in a separate thread."""
    try:
        analyzer = GitHubRepoAnalyzer(api_key)
        report_path, _ = analyzer.analyze_repository(repo_url, output_type, REPORTS_DIR)
        
        analysis_jobs[job_id]['status'] = 'completed'
        analysis_jobs[job_id]['report_path'] = report_path
        
        # Generate PDF if requested
        if generate_pdf and report_path:
            pdf_path = analyzer.export_to_pdf(report_path)
            analysis_jobs[job_id]['pdf_path'] = pdf_path
            
    except Exception as e:
        logger.error(f"Analysis failed for job {job_id}: {e}")
        analysis_jobs[job_id]['status'] = 'failed'
        analysis_jobs[job_id]['error'] = str(e)

@app.route('/')
def index():
    return render_template('index.html', jobs=analysis_jobs)

@app.route('/analyze', methods=['POST'])
def analyze():
    repo_url = request.form.get('repo_url')
    generate_pdf = 'generate_pdf' in request.form
    
    # Get output type from form
    output_type = request.form.get('output_type', 'analysis')
    if output_type not in ['analysis', 'readme', 'guidance']:
        output_type = 'analysis'  # Default to analysis if invalid type provided
    
    if not repo_url:
        flash('Please enter a GitHub repository URL', 'error')
        return redirect(url_for('index'))
    
    # Get API key from form or environment variable
    api_key = request.form.get('api_key') or os.environ.get('GEMINI_API_KEY')
    if not api_key:
        flash('Please provide a Gemini API key', 'error')
        return redirect(url_for('index'))
    
    # Generate a unique job ID
    job_id = str(uuid.uuid4())
    
    # Create job entry
    repo_name = repo_url.rstrip('/').split('/')[-1]
    if repo_name.endswith('.git'):
        repo_name = repo_name[:-4]
        
    analysis_jobs[job_id] = {
        'id': job_id,
        'repo_url': repo_url,
        'repo_name': repo_name,
        'status': 'running',
        'output_type': output_type,
        'report_path': None,
        'pdf_path': None,
        'error': None,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Start analysis in a separate thread
    thread = threading.Thread(
        target=analyze_repo_async,
        args=(job_id, repo_url, api_key, output_type, generate_pdf)
    )
    thread.daemon = True
    thread.start()
    
    report_type_name = {
        "analysis": "Analysis report",
        "readme": "README file", 
        "guidance": "Development guidance"
    }.get(output_type, "Analysis report")
    
    flash(f'{report_type_name} generation started for repository: {repo_name}', 'info')
    return redirect(url_for('index'))

@app.route('/status/<job_id>')
def job_status(job_id):
    if job_id not in analysis_jobs:
        flash('Job not found', 'error')
        return redirect(url_for('index'))
    
    return render_template('status.html', job=analysis_jobs[job_id])

@app.route('/download/<job_id>/<filetype>')
def download_report(job_id, filetype):
    if job_id not in analysis_jobs:
        flash('Job not found', 'error')
        return redirect(url_for('index'))
    
    job = analysis_jobs[job_id]
    
    if job['status'] != 'completed':
        flash('Analysis not yet completed', 'error')
        return redirect(url_for('job_status', job_id=job_id))
    
    if filetype == 'md' and job['report_path']:
        return send_file(job['report_path'], as_attachment=True)
    elif filetype == 'pdf' and job['pdf_path']:
        return send_file(job['pdf_path'], as_attachment=True)
    else:
        flash(f'Requested file ({filetype}) not available', 'error')
        return redirect(url_for('job_status', job_id=job_id))

if __name__ == '__main__':
    app.run(debug=True)