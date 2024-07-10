from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
import json
from pytube import YouTube
import os
import assemblyai as aai
from openai import OpenAI
from .models import BlogPost
from django.http import JsonResponse
import openai


# Create your views here.

@login_required
def index(request):
    return render(request, 'index.html')

@csrf_exempt
def generate_blog(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            yt_link = data.get('link')

            if not yt_link:
                return JsonResponse({'error': 'YouTube link not provided'}, status=400)

            # get yt title (assuming you have a function yt_title)
            title = yt_title(yt_link)

            # get transcript (assuming you have a function get_transcription)
            transcription = get_transcription(yt_link)
            if not transcription:
                return JsonResponse({'error': 'Failed to retrieve transcription'}, status=500)

            # generate blog content
            blog_content = generate_blog_from_transcription(transcription)
            if not blog_content:
                return JsonResponse({'error': 'Failed to generate blog content'}, status=500)

            # save blog article to database (assuming BlogPost model exists)
            new_blog_article = BlogPost.objects.create(
                user=request.user,  # Assuming user is authenticated and set properly
                youtube_title=title,
                youtube_link=yt_link,
                generated_content=blog_content
            )
            new_blog_article.save()

            # return generated blog content as response
            return JsonResponse({'content': blog_content})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format in request body'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    else:
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)


def generate_blog_from_transcription(transcription):
    try:
        prompt = f"Based on the following transcript from a YouTube video, write a comprehensive blog article:\n\n{transcription}\n\nArticle:"

        response = openai.Completion.create(
            model="gpt-3.5-turbo",
            prompt=prompt,
            max_tokens=1000
        )

        generated_content = response.choices[0].text.strip()
        return generated_content

    except Exception as e:
        raise e  # or handle as needed

def yt_title(link):
    yt = YouTube(link)
    title = yt.title
    return title

def download_audio(link):
    yt = YouTube(link)
    video = yt.streams.filter(only_audio=True).first()
    out_file = video.download(output_path=settings.MEDIA_ROOT)
    base, ext = os.path.splitext(out_file)
    new_file = base + '.mp3'
    os.rename(out_file, new_file)
    return new_file
def blog_list(request):
    blog_article = BlogPost.objects.filter(user=request.user)
    return render(request, "all-blogs.html", {'blog_articles': blog_articles})

def blog_details(request, pk):
    blog_article_detail = BlogPost.objects.get(id=pk)
    if request.user == blog_article_detail.user:
        return render(request, 'blog-details.html', {'blog_article_detail': blog_article_detail})
    else:
        return redirect('/')


def get_transcription(link):
    audio_file = download_audio(link)
    aai.settings.api_key = "938c6ea527bf4087a085aece8d2e3c77"

    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_file)

    return transcript.text

def generate_blog_from_transcription(transcription):
    client = OpenAI('sk-proj-dzAhZdm00ilE5fL59JxuT3BlbkFJLutdp0yY8HXoo9OnT0mT')

    prompt = f"Based on the following transcript from a YouTube video, write a comprehensive blog article, write it based on the transcript, but dont make it look like a youtube video, make it look like a proper blog article:\n\n{transcription}\n\nArticle:"

    response = client.Completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=1000
    )

    generated_content = response.choices[0].text.strip()

    return generated_content



def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            error_message = "Invalid username or password"
            return render(render, 'login.html', {'error_message': error_message})
    return render(request, 'login.html')

def user_signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        repeatPassword = request.POST['repeatPassword']

        if password == repeatPassword:
            try:
                user = User.objects.create_user(username, email, password)
                user.save()
                login(request, user)
                return redirect('/')
            except:
                error_message = 'Error creating account'
                return render(request, 'signup.html', {'error_message':error_message})

        else:
            error_message = 'passwords do not match'
            return render(request, 'signup.html', {'error_message':error_message})
    return render(request, 'signup.html')

def user_logout(request):
    logout(request)
    return redirect('/') 