// Mobile menu functionality
function toggleMobileMenu() {
    const navLinks = document.querySelector('.nav-links');
    const mobileBtn = document.querySelector('.mobile-menu-btn');

    if (navLinks.style.display === 'flex') {
        navLinks.style.display = 'none';
        mobileBtn.textContent = '☰';
    } else {
        navLinks.style.display = 'flex';
        navLinks.style.flexDirection = 'column';
        navLinks.style.position = 'absolute';
        navLinks.style.top = '100%';
        navLinks.style.left = '0';
        navLinks.style.right = '0';
        navLinks.style.background = 'white';
        navLinks.style.padding = '1rem 2rem';
        navLinks.style.boxShadow = 'var(--shadow)';
        navLinks.style.gap = '1rem';
        mobileBtn.textContent = '✕';
    }
}

// Tab functionality
function showTab(tabId, buttonElement) {
    // Hide all tab contents
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => content.classList.remove('active'));

    // Remove active class from all buttons
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => btn.classList.remove('active'));

    // Show selected tab and mark button as active
    const targetTab = document.getElementById(tabId);
    if (targetTab) {
        targetTab.classList.add('active');
    }

    // If buttonElement is provided, use it; otherwise try to find the clicked element
    const button = buttonElement || event?.target;
    if (button) {
        button.classList.add('active');
    }
}

// Smooth scrolling for navigation links
document.addEventListener('DOMContentLoaded', function() {
    const navLinks = document.querySelectorAll('a[href^="#"]');

    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();

            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);

            if (targetElement) {
                const headerHeight = document.querySelector('.header').offsetHeight;
                const targetPosition = targetElement.offsetTop - headerHeight - 20;

                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });

    // Close mobile menu when clicking on links
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            const navLinksElement = document.querySelector('.nav-links');
            const mobileBtn = document.querySelector('.mobile-menu-btn');

            if (window.innerWidth <= 768) {
                navLinksElement.style.display = 'none';
                mobileBtn.textContent = '☰';
            }
        });
    });
});

// Agent carousel functionality (for future enhancement)
let currentAgent = 0;
const agents = [
    {
        name: 'zen-architect',
        badge: 'Architecture',
        description: 'Designs systems with ruthless simplicity, focusing on essential patterns and clean abstractions.'
    },
    {
        name: 'bug-hunter',
        badge: 'Debugging',
        description: 'Systematic debugging approach with pattern recognition and root cause analysis.'
    },
    {
        name: 'security-guardian',
        badge: 'Security',
        description: 'Comprehensive security analysis, vulnerability detection, and best practice enforcement.'
    },
    {
        name: 'test-coverage',
        badge: 'Testing',
        description: 'Builds comprehensive test strategies with edge case identification and coverage analysis.'
    }
];

function rotateAgents() {
    const agentCard = document.querySelector('.agent-card');
    if (!agentCard) return;

    currentAgent = (currentAgent + 1) % agents.length;
    const agent = agents[currentAgent];

    agentCard.innerHTML = `
        <div class="agent-header">
            <span class="agent-name">${agent.name}</span>
            <span class="agent-badge">${agent.badge}</span>
        </div>
        <p>${agent.description}</p>
    `;
}

// Auto-rotate agents every 4 seconds
setInterval(rotateAgents, 4000);

// Copy code functionality
function addCopyButtons() {
    const codeSnippets = document.querySelectorAll('.code-snippet code');

    codeSnippets.forEach(code => {
        const wrapper = code.parentElement;
        wrapper.style.position = 'relative';

        const copyBtn = document.createElement('button');
        copyBtn.textContent = 'Copy';
        copyBtn.className = 'copy-btn';
        copyBtn.style.cssText = `
            position: absolute;
            top: 0.5rem;
            right: 0.5rem;
            background: rgba(255, 255, 255, 0.2);
            color: white;
            border: none;
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            font-size: 0.75rem;
            cursor: pointer;
            transition: background 0.2s;
        `;

        copyBtn.addEventListener('click', async () => {
            try {
                await navigator.clipboard.writeText(code.textContent);
                copyBtn.textContent = 'Copied!';
                setTimeout(() => {
                    copyBtn.textContent = 'Copy';
                }, 2000);
            } catch (err) {
                console.error('Failed to copy: ', err);
            }
        });

        copyBtn.addEventListener('mouseenter', () => {
            copyBtn.style.background = 'rgba(255, 255, 255, 0.3)';
        });

        copyBtn.addEventListener('mouseleave', () => {
            copyBtn.style.background = 'rgba(255, 255, 255, 0.2)';
        });

        wrapper.appendChild(copyBtn);
    });
}

// Initialize copy buttons when DOM is loaded
document.addEventListener('DOMContentLoaded', addCopyButtons);

// Intersection Observer for animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Initialize animations when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const animatedElements = document.querySelectorAll('.overview-item, .example-card, .step, .feature-showcase');

    animatedElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
});

// Terminal typing effect
function typeText(element, text, delay = 50) {
    let i = 0;
    element.textContent = '';

    function type() {
        if (i < text.length) {
            element.textContent += text.charAt(i);
            i++;
            setTimeout(type, delay);
        }
    }

    type();
}

// Initialize terminal animation
document.addEventListener('DOMContentLoaded', () => {
    const typingElement = document.querySelector('.typing-animation');
    if (typingElement) {
        setTimeout(() => {
            typeText(typingElement, 'Use zen-architect to design my notification system', 80);
        }, 1000);
    }
});

// Header scroll effect
let lastScrollTop = 0;
window.addEventListener('scroll', () => {
    const header = document.querySelector('.header');
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

    if (scrollTop > lastScrollTop && scrollTop > 100) {
        header.style.transform = 'translateY(-100%)';
    } else {
        header.style.transform = 'translateY(0)';
    }

    lastScrollTop = scrollTop;
});

// Add smooth transitions to header
document.addEventListener('DOMContentLoaded', () => {
    const header = document.querySelector('.header');
    header.style.transition = 'transform 0.3s ease-in-out';
});