from django.shortcuts import render, redirect
from .forms import RoomForm, UserForm, MyUserCreationForm
# Create your views here.
from django.http import HttpResponse
from .models import Room, Topic, Messages, User
from django.db.models import Q

# from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout

from django.contrib.auth.decorators import login_required

# from django.contrib.auth.forms import UserCreationForm

from django.core.paginator import Paginator

from django.conf import settings
from django.core.mail import send_mail


def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''

    rooms = Room.objects.filter(Q(topic__name__icontains=q) | Q(name__icontains=q) | Q(description__icontains=q))

    page = Paginator(rooms, 3)
    page_number = request.GET.get('page')
    page = page.get_page(page_number)


    topics = Topic.objects.all()[0:3]
    room_count = rooms.count()
    room_messages = Messages.objects.filter(Q(room__topic__name__icontains=q))[0:3]
    context = {'rooms': rooms, "topics": topics, "room_count": room_count, "room_messages": room_messages, "page": page}
    return render(request, 'base/home.html', context)


def room(request, pk):
    room = Room.objects.get(id=int(pk))
    room_messages = room.messages_set.all().order_by('-created')
    participants = room.participants.all()

    if request.method == "POST":
        message = Messages.objects.create(
            user=request.user,
            room=room,
            body=request.POST.get('body')
        )
        room.participants.add(request.user)
        return redirect('room', pk=room.id)


    context = {'room': room, "room_messages": room_messages, "participants": participants}
    return render(request, "base/room.html", context)


@login_required(login_url='login')
def create_room(request):
    form = RoomForm()
    topics = Topic.objects.all()
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description')
        )

        return redirect('home')



    context = {'form': form, 'topics': topics}
    return render(request, 'base/room_form.html', context)

@login_required(login_url='login')
def update_room(request, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()

    if request.user != room.host:
        return HttpResponse("<h1>You do not have permission!</h1>")

    if request.method == "POST":
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()
        return redirect('home')



    context = {'form': form, 'topics': topics, 'room':room}
    return render(request, 'base/room_form.html', context)

@login_required(login_url='login')
def delete_room(request, pk):
    room = Room.objects.get(id=pk)

    if request.user != room.host:
        return HttpResponse("<h1>You do not have permission!</h1>")

    if request.method == "POST":
        room.delete()
        return redirect('home')

    return render(request, "base/delete.html", {'obj': room})


def login_page(request):
    page = "login"
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, "User does not exist!")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Password is not valid...")

    context = {"page": page}
    return render(request, "base/login_register.html", context)

def logout_user(request):
    logout(request)
    return redirect('home')

def register_page(request):
    form = MyUserCreationForm()
    if request.method == "POST":
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "An error occurred during registration!")
    return render(request, "base/login_register.html", {"form": form})



@login_required(login_url='login')
def delete_message(request, pk):
    message = Messages.objects.get(id=pk)

    if request.user != message.user:
        return HttpResponse("<h1>You do not have permission!</h1>")

    if request.method == "POST":
        message.delete()
        return redirect('home')

    return render(request, "base/delete.html", {'obj': message})

def user_profile(request, pk):
    profile = True
    user = User.objects.get(id=pk)
    topics = Topic.objects.all()
    rooms = user.room_set.all()
    room_messages = user.messages_set.all()

    page = Paginator(rooms, 3)
    page_number = request.GET.get('page')
    page = page.get_page(page_number)

    if request.method == 'POST':
        info = f"""
        Sender: {request.user.username}
        Email: {request.user.email}
        """
        title = request.POST['title']
        message = request.POST['message'] + info
        email = user.email


        send_mail(subject=title, message=message, from_email=settings.EMAIL_HOST_USER,
                  recipient_list=[email], fail_silently=False)

    context = {"user": user, "topics": topics, "rooms": rooms,
               "room_messages": room_messages, 'page': page, 'profile': profile}
    return render(request, "base/profile.html", context)


@login_required(login_url='login')
def update_user(request):
    user = request.user
    form = UserForm(instance=user)

    if request.method == "POST":
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)

    return render(request, "base/update_user.html", {'form': form})


def topics_page(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(name__icontains=q)
    context = {'topics': topics}
    return render(request, "base/topics.html", context)


def activity_page(request):
    room_messages = Messages.objects.all()
    context = {"room_messages": room_messages}
    return render(request, "base/activity.html", context)

