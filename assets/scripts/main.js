// main.js
document.addEventListener('DOMContentLoaded', function() {
    fetch('./data.json')
        .then(response => response.json())
        .then(data => {
            const postList = document.getElementById('postList');
            data.forEach(post => {
                const listItem = document.createElement('li');
                const link = document.createElement('a');
                link.href = post.url;
                link.textContent = post.title;
                listItem.appendChild(link);
                postList.appendChild(listItem);
            });
        })
        .catch(error => console.error('Error loading the blog posts:', error));
});

// Smooth Scrolling for Navigation Links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const targetElement = document.querySelector(this.getAttribute('href'));
        if (targetElement) {
            targetElement.scrollIntoView({ behavior: 'smooth' });
        }
    });
});

// Trigger Animation on Scroll
const animatedElements = document.querySelectorAll('.animate-on-scroll');
const observer = new IntersectionObserver(
    entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    },
    { threshold: 0.1 } // Customize this threshold to control when animations trigger
);

animatedElements.forEach(element => observer.observe(element));

// Placeholder for additional interactive behaviors
