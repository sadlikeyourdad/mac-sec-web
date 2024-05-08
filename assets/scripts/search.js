document.getElementById('searchBar').addEventListener('input', function () {
    const searchText = this.value.toLowerCase();
    const postListItems = document.querySelectorAll('#postList li');
    postListItems.forEach(item => {
        const postText = item.textContent.toLowerCase();
        if (postText.includes(searchText)) {
            item.style.display = '';
        } else {
            item.style.display = 'none';
        }
    });
});
