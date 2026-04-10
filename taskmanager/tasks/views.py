from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .models import Task


# AUTH VIEWS
def register_view(request):
    if request.method == "POST":
        # instantiate the form with the data sent by the user
        form = UserCreationForm(request.POST)
        if form.is_valid():
            # save the user to the database and return the User object
            user = form.save()
            # auto login after registration, avoids redirecting to login page
            login(request, user)
            return redirect("task-list")
    else:
        # GET: instantiate empty form to display on the page
        form = UserCreationForm()

    # render the template passing the form — both on GET and invalid POST
    # on invalid POST, the form already carries the validation errors
    return render(request, "registration/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        # AuthenticationForm receives request as first argument (unlike UserCreationForm)
        # this is required because it uses the request to authenticate via backend
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            # get_user() returns the user authenticated by the form
            # do not use request.user here — it is still anonymous at this point
            user = form.get_user()
            # creates the user session on the server and sets the cookie in the browser
            login(request, user)
            return redirect("task-list")
    else:
        form = AuthenticationForm()
    return render(request, "registration/login.html", {"form": form})


def logout_view(request):
    # destroys the user session on the server and clears the cookie
    logout(request)
    return redirect("login")


# TASK VIEWS
class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = "tasks/list.html"
    context_object_name = "tasks"

    def get_queryset(self):
        # return only tasks that belong to the logged-in user
        return Task.objects.filter(user=self.request.user)


class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    template_name = "tasks/form.html"
    fields = ["title", "description", "status"]
    success_url = reverse_lazy("task-list")

    def form_valid(self, form):
        # inject the logged-in user before saving the form
        form.instance.user = self.request.user
        return super().form_valid(form)


class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    template_name = "tasks/form.html"
    fields = ["title", "description", "status"]
    success_url = reverse_lazy("task-list")

    def get_queryset(self):
        # ensure the user can only edit their own tasks
        return Task.objects.filter(user=self.request.user)


class TaskDeleteView(LoginRequiredMixin, DeleteView):
    model = Task
    template_name = "tasks/confirm_delete.html"
    success_url = reverse_lazy("task-list")

    def get_queryset(self):
        # ensure the user can only delete their own tasks
        return Task.objects.filter(user=self.request.user)
