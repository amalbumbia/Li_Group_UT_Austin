/**
 * Universal header loader for both local development and GitHub Pages
 * This script will:
 * 1. Detect whether we're on GitHub Pages or local development
 * 2. Calculate the correct path to the header file
 * 3. Load the header content
 * 4. Fix relative paths in the header based on current page location
 */
document.addEventListener('DOMContentLoaded', function() {
    // Debug information to console
    console.log('Header loader running');
    console.log('Current URL:', window.location.href);
    
    // Detect GitHub Pages vs local development
    const isGitHubPages = window.location.hostname.includes('amalbumbia.github.io');
    console.log('Environment:', isGitHubPages ? 'GitHub Pages' : 'Local development');
    
    // Get repository name (needed for GitHub Pages path calculation)
    function getRepoName() {
        if (!isGitHubPages) return '';
        
        const pathParts = window.location.pathname.split('/');
        // GitHub Pages URL format: username.github.io/repo-name/...
        return pathParts.length > 1 ? pathParts[1] : '';
    }
    
    // Calculate path to root directory based on current location
    function getPathToRoot() {
        // Get current path
        const fullPath = window.location.pathname;
        const repoName = getRepoName();
        
        // For GitHub Pages, remove repo name from path calculation
        let pathWithoutRepo = fullPath;
        if (isGitHubPages && repoName) {
            // Remove leading slash and repo name
            const repoPath = '/' + repoName;
            pathWithoutRepo = fullPath.startsWith(repoPath) ? 
                              fullPath.substring(repoPath.length) : 
                              fullPath;
        }
        
        // Split by '/' and remove empty entries
        const parts = pathWithoutRepo.split('/').filter(part => part !== '');
        
        // If we're at root or index.html at root, return appropriate path
        if (parts.length === 0 || (parts.length === 1 && parts[0] === 'index.html')) {
            return isGitHubPages && repoName ? '/' + repoName + '/' : './';
        }
        
        // For files in subdirectories, calculate relative path to root
        // Number of "../" needed equals the depth of the current page
        const depth = parts.length - (parts[parts.length-1].includes('.') ? 1 : 0);
        const relativePath = '../'.repeat(depth);
        
        // Return the appropriate path prefix
        return isGitHubPages && repoName ? 
               '/' + repoName + '/' : 
               relativePath;
    }
    
    // Get path to root
    const pathToRoot = getPathToRoot();
    console.log('Path to root:', pathToRoot);
    
    // Path to header file
    const headerPath = pathToRoot.endsWith('/') ? 
                      pathToRoot + 'header.html' : 
                      pathToRoot + '/header.html';
    console.log('Header path:', headerPath);
    
    // Fetch the header content
    fetch(headerPath)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to load header (${response.status}: ${response.statusText})`);
            }
            return response.text();
        })
        .then(data => {
            // Insert header content
            const headerPlaceholder = document.getElementById('header-placeholder');
            if (!headerPlaceholder) {
                console.error('No header placeholder found. Add <div id="header-placeholder"></div> to your HTML.');
                return;
            }
            
            headerPlaceholder.innerHTML = data;
            
            // Fix paths in the header 
            document.querySelectorAll('#header-placeholder a').forEach(link => {
                const href = link.getAttribute('href');
                
                // Skip non-relevant links
                if (!href || href === '#' || href.startsWith('http') || href.startsWith('mailto:')) {
                    return;
                }
                
                // Don't modify dropdown toggle
                if (link.classList.contains('dropdown-toggle')) {
                    return;
                }
                
                // Fix relative paths
                if (href.startsWith('./') || href.startsWith('../')) {
                    // Already relative - leave as is
                    return;
                } else if (href.startsWith('/')) {
                    // Absolute path from root - add repo name for GitHub Pages
                    if (isGitHubPages && getRepoName()) {
                        link.href = '/' + getRepoName() + href;
                    }
                } else {
                    // Plain relative path - add path to root
                    const newPath = pathToRoot.endsWith('/') ? 
                                  pathToRoot + href : 
                                  pathToRoot + '/' + href;
                    link.href = newPath;
                }
            });
            
            // Initialize mobile menu functionality
            const mobileToggle = document.querySelector('.mobile-nav-toggle');
            const mainNav = document.querySelector('.main-nav');
            
            if (mobileToggle && mainNav) {
                mobileToggle.addEventListener('click', function() {
                    mainNav.classList.toggle('active');
                });
            }
            
            // Dropdown functionality for mobile
            const dropdowns = document.querySelectorAll('.dropdown');
            dropdowns.forEach(dropdown => {
                const toggle = dropdown.querySelector('.dropdown-toggle');
                if (toggle && window.innerWidth <= 800) {
                    toggle.addEventListener('click', function(e) {
                        e.preventDefault();
                        dropdown.classList.toggle('active');
                    });
                }
            });
            
            console.log('Header loaded successfully');
        })
        .catch(error => {
            console.error('Error loading header:', error);
            console.log('Tried to load from:', headerPath);
            
            // Provide fallback or alternative error handling
            const headerPlaceholder = document.getElementById('header-placeholder');
            if (headerPlaceholder) {
                headerPlaceholder.innerHTML = `
                    <div class="site-header" style="background-color: #1a237e; color: white; padding: 0 40px; height: 70px; display: flex; align-items: center;">
                        <div style="font-weight: bold; font-size: 0.4em;">
                            <a href="${pathToRoot}" style="color: white; text-decoration: none;">Relativistic Electrodynamics</a>
                        </div>
                    </div>
                `;
            }
        });
});