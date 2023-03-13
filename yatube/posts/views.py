from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect

from .models import Follow, Group, Post, User
from .forms import CommentForm, PostForm
from .utils import make_page


@login_required
def post_create(request):
    '''Создание поста под авторизацией.'''
    if request.method == "POST":
        form = PostForm(request.POST, files=request.FILES or None)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', request.user)
    form = PostForm()
    return render(
        request,
        'posts/create_post.html',
        {
            'form': form,
        },
    )


@login_required
def post_edit(request, post_id):
    '''Редактирование поста под авторизацией.'''
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post
    )
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id)
    return render(
        request,
        'posts/create_post.html',
        {'form': form, 'is_edit': True},
    )


# @cache_page(20, key_prefix='index_page')
def index(request):
    '''Главная страница c кешем 20 секунд.'''
    posts = Post.objects.select_related('group', 'author')
    return render(
        request, 'posts/index.html', {'page_obj': make_page(request, posts)}
    )


def group_posts(request, slug):
    '''Страница групп.'''
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author')
    return render(
        request,
        'posts/group_list.html',
        {'group': group, 'page_obj': make_page(request, posts)},
    )


def profile(request, username):
    '''Страница профиля пользователя.'''
    author = get_object_or_404(User, username=username)
    posts = Post.objects.select_related('group', 'author').filter(
        author__username=username
    )

    following = False
    if request.user.is_authenticated and author != request.user:
        following = Follow.objects.filter(
            user=request.user, author=author
        ).exists()
    return render(
        request,
        'posts/profile.html',
        {
            'author': author,
            'page_obj': make_page(request, posts),
            'following': following,
        },
    )


def post_detail(request, post_id):
    '''Отдельная запись.'''
    post = get_object_or_404(
        Post.objects.select_related('author', 'group'), id=post_id
    )
    comments = post.comments.all().select_related('author')
    form = CommentForm()
    author = request.user.id
    return render(
        request,
        'posts/post_detail.html',
        {
            'post': post,
            'author': author,
            'form': form,
            'comments': comments,
        },
    )


@login_required
def add_comment(request, post_id):
    '''Добавление комментариев под авторизацией'''
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = get_object_or_404(Post, id=post_id)
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    '''Страница постов автора, на которого подписан пользователь'''
    posts = Post.objects.filter(author__following__user=request.user)
    return render(
        request,
        'posts/follow.html',
        {
            'page_obj': make_page(request, posts),
        },
    )


@login_required
def profile_follow(request, username):
    """Функция подписывания на автора."""
    author = User.objects.get(username=username)
    if (
        request.user != author
        and not Follow.objects.filter(
            user=request.user, author=author
        ).exists()
    ):
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    """Функция отписывания от автора"""
    author = User.objects.get(username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=username)
