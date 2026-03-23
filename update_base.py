
content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Wrapp Delights - Corporate Catalog{% endblock %}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        brand: {
                            red: '#C8102E', // Grainger red style
                            dark: '#8B0A1E',
                            gray: '#f5f5f5',
                        }
                    },
                    fontFamily: {
                        sans: ['Inter', 'Arial', 'sans-serif'],
                    },
                    fontSize: {
                        'xxs': '0.65rem',
                    }
                }
            }
        }
    </script>
    <style>
        body { font-family: 'Inter', Arial, sans-serif; -webkit-font-smoothing: antialiased; }
        .mega-menu { display: none; }
        .group:hover .mega-menu { display: block; }
        /* Sharp edges preference */
        * { border-radius: 0 !important; }
        .rounded-none { border-radius: 0 !important; }
        /* Form inputs focus ring color */
        input:focus { outline: none; border-color: #C8102E; ring: 1px #C8102E; }
    </style>
</head>
<body class="bg-white text-gray-900 flex flex-col min-h-screen">

    <!-- 1. THIN TOP BAR -->
    <div class="bg-gray-100 border-b border-gray-200 text-xs py-1.5 text-gray-600">
        <div class="container mx-auto px-4 flex justify-between items-center">
            <div class="flex gap-6">
                <span><span class="font-bold text-gray-800">Call Us:</span> 1-800-WRAPP-DL</span>
                <span><span class="font-bold text-gray-800">Email:</span> sales@wrappdelights.com</span>
                <span class="hidden sm:inline"><span class="font-bold text-gray-800">Location:</span> Mumbai, India</span>
            </div>
            <div class="flex gap-4">
                <a href="#" class="hover:text-brand-red">Help Center</a>
                <a href="#" class="hover:text-brand-red">Track Inquiry</a>
                {% if user.is_authenticated %}
                    <a href="{% url 'account' %}" class="font-bold text-brand-red">My Account</a>
                    <a href="{% url 'logout' %}" class="hover:text-brand-red">Sign Out</a>
                {% else %}
                    <a href="{% url 'login' %}" class="font-bold text-brand-red">Sign In / Register</a>
                {% endif %}
            </div>
        </div>
    </div>

    <!-- 2. MAIN HEADER -->
    <header class="bg-white py-5 border-b border-gray-200 sticky top-0 z-50 shadow-sm">
        <div class="container mx-auto px-4 flex items-center justify-between gap-8">
            <!-- LOGO -->
            <a href="/" class="flex-shrink-0">
                <div class="text-2xl font-extrabold tracking-tighter text-brand-red">
                    WRAPP<span class="text-gray-900">DELIGHTS</span>
                </div>
                <div class="text-[0.6rem] font-bold text-gray-500 tracking-widest uppercase -mt-1">Corporate Catalog</div>
            </a>

            <!-- SEARCH BAR (DOMINANT) -->
            <div class="flex-grow max-w-3xl relative">
                <form action="{% url 'products' %}" method="get" class="flex w-full">
                    <div class="relative w-full">
                        <input type="text" name="q" placeholder="Search by keyword, SKU, or category..." 
                            class="w-full h-10 pl-4 pr-10 border border-gray-400 bg-gray-50 text-sm focus:bg-white focus:border-brand-red transition-colors placeholder-gray-500"
                            value="{{ request.GET.q }}">
                        <button type="submit" class="absolute right-0 top-0 h-10 w-10 flex items-center justify-center text-gray-600 hover:text-brand-red">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="square" stroke-linejoin="miter" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                            </svg>
                        </button>
                    </div>
                </form>
            </div>

            <!-- RIGHT ACTIONS -->
            <div class="flex items-center gap-6 flex-shrink-0">
                <div class="flex flex-col items-end">
                    <span class="text-xs text-gray-500">Need a quote?</span>
                    <a href="https://wa.me/{{ phone_number_raw|default:whatsapp_number|default:'919999999999' }}?text={{ 'Hi, I want a quote from your catalog. Please share available SKUs and delivery timeline.'|urlencode }}" 
                       target="_blank" 
                       class="text-sm font-bold text-brand-red hover:underline flex items-center gap-1">
                        Request Quote
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="square" stroke-linejoin="miter" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                        </svg>
                    </a>
                </div>
                <div class="border-l border-gray-300 h-8"></div>
                <a href="{% url 'account' %}" class="flex flex-col items-center group">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-gray-700 group-hover:text-brand-red" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="square" stroke-linejoin="miter" stroke-width="1.5" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                    <span class="text-[10px] uppercase font-bold text-gray-600 mt-1">Account</span>
                </a>
            </div>
        </div>
    </header>

    <!-- 3. NAVBAR (CATEGORIES) -->
    <nav class="bg-brand-red text-white text-sm font-medium border-b border-brand-dark shadow-sm">
        <div class="container mx-auto px-4">
            <div class="flex items-center">
                <a href="{% url 'products' %}" class="px-5 py-3 bg-brand-dark hover:bg-black transition-colors flex items-center gap-2 uppercase font-bold text-xs tracking-wide">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="square" stroke-linejoin="miter" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
                    </svg>
                    All Categories
                </a>
                <div class="flex overflow-x-auto no-scrollbar">
                    {% for cat in categories|slice:":8" %}
                        <a href="{% url 'products' %}?category={{ cat.slug }}" class="px-5 py-3 hover:bg-brand-dark transition-colors whitespace-nowrap border-r border-brand-dark border-opacity-30">
                            {{ cat.name }}
                        </a>
                    {% endfor %}
                    <a href="{% url 'products' %}" class="px-5 py-3 hover:bg-brand-dark transition-colors whitespace-nowrap italic">
                        View All...
                    </a>
                </div>
            </div>
        </div>
    </nav>

    <!-- MAIN CONTENT -->
    <main class="flex-grow bg-white">
        {% if messages %}
            <div class="container mx-auto px-4 mt-4">
                {% for message in messages %}
                    <div class="p-4 mb-4 text-sm text-blue-800 bg-blue-50 border border-blue-200" role="alert">
                        {{ message }}
                    </div>
                {% endfor %}
            </div>
        {% endif %}

        {% block content %}{% endblock %}
    </main>

    <!-- FOOTER -->
    <footer class="bg-gray-900 text-gray-400 text-sm mt-12 pt-12 pb-6 border-t border-brand-red">
        <div class="container mx-auto px-4 grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
            <div>
                <div class="text-xl font-extrabold text-white mb-4 tracking-tighter">WRAPP<span class="text-brand-red">DELIGHTS</span></div>
                <p class="mb-4 text-xs leading-relaxed">
                    Premium corporate gifting solutions for businesses. 
                    Bulk orders, custom branding, and nationwide delivery.
                </p>
                <div class="flex gap-4">
                    <!-- Social icons placeholder -->
                </div>
            </div>
            <div>
                <h3 class="text-white font-bold uppercase tracking-wider text-xs mb-4">Customer Service</h3>
                <ul class="space-y-2 text-xs">
                    <li><a href="#" class="hover:text-white">Contact Us</a></li>
                    <li><a href="#" class="hover:text-white">Request a Quote</a></li>
                    <li><a href="#" class="hover:text-white">Shipping Policy</a></li>
                    <li><a href="#" class="hover:text-white">Returns & Warranty</a></li>
                    <li><a href="#" class="hover:text-white">FAQs</a></li>
                </ul>
            </div>
            <div>
                <h3 class="text-white font-bold uppercase tracking-wider text-xs mb-4">Product Categories</h3>
                <ul class="space-y-2 text-xs">
                    {% for cat in categories|slice:":5" %}
                        <li><a href="{% url 'products' %}?category={{ cat.slug }}" class="hover:text-white">{{ cat.name }}</a></li>
                    {% endfor %}
                </ul>
            </div>
            <div>
                <h3 class="text-white font-bold uppercase tracking-wider text-xs mb-4">Contact</h3>
                <ul class="space-y-2 text-xs">
                    <li class="flex items-start gap-2">
                        <span class="text-brand-red font-bold">T:</span> 1-800-WRAPP-DL
                    </li>
                    <li class="flex items-start gap-2">
                        <span class="text-brand-red font-bold">E:</span> sales@wrappdelights.com
                    </li>
                    <li class="flex items-start gap-2">
                        <span class="text-brand-red font-bold">A:</span> Mumbai, Maharashtra, India
                    </li>
                </ul>
            </div>
        </div>
        <div class="container mx-auto px-4 pt-6 border-t border-gray-800 flex flex-col md:flex-row justify-between items-center text-xs">
            <div>&copy; {% now "Y" %} Wrapp Delights. All rights reserved. B2B Catalog.</div>
            <div class="flex gap-4 mt-2 md:mt-0">
                <a href="#" class="hover:text-white">Privacy Policy</a>
                <a href="#" class="hover:text-white">Terms of Use</a>
            </div>
        </div>
    </footer>

</body>
</html>"""

with open(r'c:\Users\adity\OneDrive\Desktop\Wrapp Delights\delights_backend\core\store\templates\base.html', 'w', encoding='utf-8') as f:
    f.write(content)
