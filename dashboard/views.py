import subprocess
import os
from django.shortcuts import render, redirect, get_object_or_404
from .models import Domain, FileURL
# Create your views here.


def fetch_data(request):
    if request.method == 'POST':
        domain_name = request.POST['domain']
        domain, _ = Domain.objects.get_or_create(name=domain_name)

        # Run curl command
        txt_file = f"{domain_name}.txt"
        curl_command = [
            "curl", "-G", "https://web.archive.org/cdx/search/cdx",
            "--data-urlencode", f"url=*.{domain_name}/*",
            "--data-urlencode", "collapse=urlkey",
            "--data-urlencode", "output=text",
            "--data-urlencode", "fl=original",
            "-o", txt_file
        ]
        subprocess.run(curl_command)

        # Filter file URLs
        print("Reading file for filtration")
        with open(txt_file, 'r', encoding='utf-8') as file:
            urls = file.readlines()

        extensions = [
            'xls', 'xml', 'xlsx', 'json', 'pdf', 'sql', 'doc', 'docx', 'pptx',
            'txt', 'zip', 'tar.gz', 'tgz', 'bak', '7z', 'rar', 'log', 'cache',
            'secret', 'db', 'backup', 'yml', 'gz', 'config', 'csv', 'yaml',
            'md', 'md5', 'exe', 'dll', 'bin', 'ini', 'bat', 'sh', 'tar', 'deb',
            'rpm', 'iso', 'img', 'apk', 'msi', 'dmg', 'tmp', 'crt', 'pem', 'key',
            'pub', 'asc'
        ]
        for url in urls:
            url = url.strip()
            for ext in extensions:
                if url.endswith(f".{ext}"):
                    FileURL.objects.create(domain=domain, file_type=ext, url=url)

        os.remove(txt_file)
        print("filtration done! Now redirecting")
        return redirect('dashboard')

    return render(request, 'fetch_data.html')

def domain_extensions(request, domain_id):
    domain = get_object_or_404(Domain, id=domain_id)
    file_urls = domain.file_urls.all()

    # Count extensions
    extensions = {}
    for file_url in file_urls:
        ext = file_url.file_type
        if ext in extensions:
            extensions[ext] += 1
        else:
            extensions[ext] = 1

    context = {
        'domain': domain,
        'extensions': extensions,
    }
    return render(request, 'extensions.html', context)


def dashboard(request):
    # Fetch all domains from the database
    domains = Domain.objects.all()

    # Pass the domains to the template
    context = {
        'domains': domains
    }
    return render(request, 'dashboard.html', context)

# def dashboard(request):
#     domains = Domain.objects.all()
#     domain_data = []

#     for domain in domains:
#         file_types = domain.file_urls.values_list('file_type', flat=True).distinct()
#         domain_data.append({
#             'domain': domain,
#             'file_types': file_types
#         })

#     context = {'domain_data': domain_data}
#     return render(request, 'dashboard.html', context)


def filter_urls(request, domain_id, file_type):
    domain = get_object_or_404(Domain, id=domain_id)
    urls = domain.file_urls.filter(file_type=file_type)

    context = {
        'domain': domain,
        'file_type': file_type,
        'urls': urls,
    }
    return render(request, 'filter_urls.html', context)

