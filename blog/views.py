import os
from os import listdir
from os.path import isfile, join
import fitz  # pip install PyMuPDF
from django.contrib import messages
from django.core import serializers as c_serializers
import re
import xlsxwriter
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import FormView
from rest_framework import renderers
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from blog.forms import DocumentForm
from blog.models import Document
from plagiarismChecker import settings
from plagiarismChecker.settings import MEDIA_ROOT, STATICFILES_DIRS
from .checker_algorithm import documentSimilarity


# Create your views here.


class UploadFileView(FormView):
    form_class = DocumentForm
    template_name = 'blog/plagiarism_checker.html'  # Replace with your template.
    success_url = '/'

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        # import pdb;pdb.set_trace()
        files = request.FILES.getlist('document')
        if form.is_valid():
            for f in files:
                handle_uploaded_file(f)
                document = Document(
                    document="documents/" + f.name
                )
                document.save()
            messages.warning(request, 'File uploaded successfully')
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get(self, request, *args, **kwargs):
        onlyfiles = ["documents/" + f for f in listdir(MEDIA_ROOT + "/documents") if
                     isfile(join(MEDIA_ROOT + "/documents", f))]
        # import pdb;pdb.set_trace()
        items = Document.objects.filter(document__in=onlyfiles)
        items = c_serializers.serialize("python", items)
        return render(request, template_name=self.template_name, context={'files': items})


def handle_uploaded_file(f):
    destination = MEDIA_ROOT + "/documents"
    with open(destination + "/" + f.name, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)


@api_view(['POST'])
def delete_file(request):
    data = request.POST
    os.remove("demofile.txt")


class DeleteFile(APIView):
    permission_classes = (AllowAny,)
    template_name = 'blog/plagiarism_checker.html'
    renderer_classes = [renderers.TemplateHTMLRenderer, ]

    def get(self, request, pk):
        try:
            item = Document.objects.filter().get(pk=pk)
            os.remove(MEDIA_ROOT + '/' + str(item.document))
            item.delete()
            messages.warning(request, 'File deleted')
        except:
            messages.warning(request, 'Unable to delete')

        return HttpResponseRedirect(reverse('file_upload'))


class CompareFile(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        base_file_id = request.GET.get('base_file')
        document = Document.objects.get(pk=base_file_id)
        comparable_documents = Document.objects.exclude(pk=base_file_id)
        try:
            with fitz.open(MEDIA_ROOT + '/' + str(document.document)) as doc:
                text = ""
                for page in doc:
                    text += page.getText()

            text = re.sub(r'[^A-Za-z \n0-9]', '', text)

            print(text)
            if text:
                f = open(MEDIA_ROOT + "/documents/temp/" + str(document.document).split('/')[1].split('.')[0] + ".txt", "w",
                         encoding="utf-8", errors="surrogateescape")

                f.write(text)
                f.close()

                # import pdb;pdb.set_trace()
            else:
                messages.warning(request, "Invalid PDF" + str(document.document))
        except:
            messages.warning(request, "Invalid PDF" + str(document.document))



        # import pdb;pdb.set_trace()
        try:
            base_res_loc = STATICFILES_DIRS[0]
            relative_path = "/documents/results/" + str(document.document).split('/')[1].split('.')[0] + ".xlsx"
            workbook = xlsxwriter.Workbook(
                base_res_loc + "/documents/results/" + str(document.document).split('/')[1].split('.')[0] + ".xlsx")
            worksheet = workbook.add_worksheet()

            row = 0
            col = 0
            worksheet.write(row, col, "Base File")
            worksheet.write(row, col + 1, "Comparing File")
            worksheet.write(row, col + 2, "Similarity")
            row += 1
            for other_doc in comparable_documents:

                with fitz.open(MEDIA_ROOT + '/' + str(other_doc.document)) as doc:
                    text = ""
                    for page in doc:
                        text += page.getText()
                # import pdb;pdb.set_trace()
                text = re.sub(r'[^A-Za-z \n0-9]', '', text)

                print(text)

                if text:
                    f = open(MEDIA_ROOT + "/documents/temp/" + str(other_doc.document).split('/')[1].split('.')[0] + ".txt",
                             "w")
                    f.write(text)
                    f.close()

                    file_1 = MEDIA_ROOT + "/documents/temp/" + str(other_doc.document).split('/')[1].split('.')[0] + ".txt"
                    file_2 = MEDIA_ROOT + "/documents/temp/" + str(document.document).split('/')[1].split('.')[0] + ".txt"

                    # import pdb;pdb.set_trace()
                    similarity = documentSimilarity(file_1, file_2)

                    worksheet.write(row, col, str(document.document))
                    worksheet.write(row, col + 1, str(other_doc.document))
                    worksheet.write(row, col + 2, similarity)
                    row += 1
                    os.remove(file_1)
                else:
                    messages.warning(request, "Invalid PDF"+str(other_doc.document))
            workbook.close()
            os.remove(MEDIA_ROOT + "/documents/temp/" + str(document.document).split('/')[1].split('.')[0] + ".txt")

            messages.warning(request, relative_path)
        except:
            messages.warning(request, "")

        return HttpResponseRedirect(reverse('file_upload'))