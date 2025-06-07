import subprocess
import os
from django.shortcuts import render, redirect, get_object_or_404
from concurrent.futures import ThreadPoolExecutor
from .models import Domain, FileURL, FileExtension, SensitiveJSFile
import re

def process_url_chunk(domain, urls, extensions, sensitive_js_files):
    """Processes a chunk of URLs to filter by extensions and sensitive JS files, then saves them to the database."""
    for url in urls:
        url = url.strip()

        # Check for sensitive file extensions
        for ext in extensions:
            if url.endswith(f".{ext}"):
                FileURL.objects.create(domain=domain, file_type=ext, url=url)

        # Check for sensitive JavaScript file names
        for js_file in sensitive_js_files:
            if url.endswith(js_file):
                FileURL.objects.create(domain=domain, file_type="js_sensitive", url=url)


def fetch_data(request):
    if request.method == "POST":
        domain_name = request.POST["domain"]
        domain, _ = Domain.objects.get_or_create(name=domain_name)

        txt_file = f"{domain_name}.txt"
        curl_command = [
            "curl", "-G", "https://web.archive.org/cdx/search/cdx",
            "--data-urlencode", f"url=*.{domain_name}/*",
            "--data-urlencode", "collapse=urlkey",
            "--data-urlencode", "output=text",
            "--data-urlencode", "fl=original",
            "-o", txt_file,
        ]
        subprocess.run(curl_command)

        try:
            with open(txt_file, "r", encoding="utf-8") as file:
                urls = file.readlines()
        except:
            with open(txt_file, "r") as file:
                urls = file.readlines()

        # Fetch from database
        extensions = list(FileExtension.objects.values_list("extension", flat=True))
        sensitive_js_files = list(SensitiveJSFile.objects.values_list("filename", flat=True))

        def process_url_chunk(domain, chunk):
            for url in chunk:
                clean_url = url.strip()
                for ext in extensions:
                    if clean_url.endswith(f".{ext}"):
                        FileURL.objects.create(domain=domain, file_type=ext, url=clean_url)
                        break
                else:
                    for js_file in sensitive_js_files:
                        if clean_url.endswith(js_file):
                            FileURL.objects.create(domain=domain, file_type="js", url=clean_url)
                            break

        num_threads = 5
        chunk_size = len(urls) // num_threads or 1
        url_chunks = [urls[i:i+chunk_size] for i in range(0, len(urls), chunk_size)]

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            for chunk in url_chunks:
                executor.submit(process_url_chunk, domain, chunk)

        os.remove(txt_file)
        return redirect("dashboard")

    return render(request, "fetch_data.html")




def manage_filters(request):
    if request.method == "POST":
        if "add_extension" in request.POST:
            new_ext = request.POST.get("new_extension", "").strip()
            if new_ext and not FileExtension.objects.filter(extension=new_ext).exists():
                FileExtension.objects.create(extension=new_ext)

        elif "delete_extension_id" in request.POST:
            FileExtension.objects.filter(id=request.POST.get("delete_extension_id")).delete()

        elif "add_js_file" in request.POST:
            new_js = request.POST.get("new_js_file", "").strip()
            if new_js and not SensitiveJSFile.objects.filter(filename=new_js).exists():
                SensitiveJSFile.objects.create(filename=new_js)

        elif "delete_js_file_id" in request.POST:
            SensitiveJSFile.objects.filter(id=request.POST.get("delete_js_file_id")).delete()

        return redirect("manage_filters")

    context = {
        "extensions": FileExtension.objects.all(),
        "js_files": SensitiveJSFile.objects.all()
    }
    return render(request, "manage_filters.html", context)




# def process_url_chunk(domain, urls, extensions):
#     """Processes a chunk of URLs to filter and save them to the database."""
#     for url in urls:
#         url = url.strip()
#         for ext in extensions:
#             if url.endswith(f".{ext}"):
#                 FileURL.objects.create(domain=domain, file_type=ext, url=url)


# def fetch_data(request):
#     if request.method == "POST":
#         domain_name = request.POST["domain"]
#         domain, _ = Domain.objects.get_or_create(name=domain_name)

#         # Run curl command to fetch URLs
#         txt_file = f"{domain_name}.txt"
#         curl_command = [
#             "curl", "-G", "https://web.archive.org/cdx/search/cdx",
#             "--data-urlencode", f"url=*.{domain_name}/*",
#             "--data-urlencode", "collapse=urlkey",
#             "--data-urlencode", "output=text",
#             "--data-urlencode", "fl=original",
#             "-o", txt_file,
#         ]
#         subprocess.run(curl_command)

#         # Read file and filter URLs using multi-threading
#         print("Reading file for filtration")
#         with open(txt_file, "r", encoding="utf-8") as file:
#             urls = file.readlines()

#         # Updated list of extensions
#         extensions = [
#             "asp", "aspx", "jsp", "cgi", "py", "pl", "rb", "sh", "bat", "ps1",
#             "exe", "dll", "jar", "war", "swf",
#             "zip", "tar", "gz", "bz2", "7z", "rar",
#             "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "rtf", "txt", "csv",
#             "mdb", "accdb", "sqlite", "db", "db3",
#             "yml", "yaml", "htaccess", "htpasswd", "ini", "conf", "env", "config", "properties",
#             "bak", "old", "swp", "tmp",
#             "sln", "cs", "csproj", "vb", "vbproj", "java", "class",
#             "pem", "crt", "key",
#             "dmp", "idb", "pdb",
#             "psd", "ai",
#         ]

#         # Number of threads
#         print("executing multiple threads!")
#         num_threads = 5
#         chunk_size = len(urls) // num_threads

#         # Split URLs into chunks for threading
#         url_chunks = [urls[i : i + chunk_size] for i in range(0, len(urls), chunk_size)]

#         # Process chunks using ThreadPoolExecutor
#         with ThreadPoolExecutor(max_workers=num_threads) as executor:
#             for chunk in url_chunks:
#                 executor.submit(process_url_chunk, domain, chunk, extensions)

#         # Remove the temporary .txt file after processing
#         os.remove(txt_file)
#         print("Filtration done! Now redirecting")
#         return redirect("dashboard")

#     return render(request, "fetch_data.html")


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


def about(request):
    return render(request, 'about.html')


def delete_domain(request, domain_id):
    domain = get_object_or_404(Domain, id=domain_id)
    domain.delete()
    return redirect('dashboard')



def filter_urls(request, domain_id, file_type):
    domain = get_object_or_404(Domain, id=domain_id)
    urls = domain.file_urls.filter(file_type=file_type)

    context = {
        'domain': domain,
        'file_type': file_type,
        'urls': urls,
    }
    return render(request, 'filter_urls.html', context)

