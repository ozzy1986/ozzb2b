=== WP-Script Core ===

== Changelog ==

= 2.0.7 = Released on 2020-08-14
* Fixed: cURL error 28 that prevented the WP-Script dashboard to load properly

= 2.0.6 = Released on 2020-08-12
* Fixed: jQuery().live is not a function since WordPress 5.5

= 2.0.5 = Released on 2020-08-11
* Added: Twitter + Discord next to WP-Script logo
* Fixed: Plugin dropdown menu displayed behind some elements

= 2.0.4 = Released on 2020-06-26
* Fixed: 403 errors with admin-ajax.php when Wordfence is activated

= 2.0.3 = Released on 2020-04-14
* Updated: Remove SSL verification on init
* Fixed: Remove dependencies for plugins icons

= 2.0.2 = Released on 2019-11-25
* Updated: Thumbs and Partners columns are back in admin posts listings
* Fixed: WP_Filesystem() PHP Fatal Error

= 2.0.1 = Released on 2019-11-21
* Fixed: Issues to update products data which prevented some installation and update features to work properly

= 2.0.0 = Released on 2019-11-19
* Added: New WPSCORE_Api class
* Added: New WPSCORE_Log class
* Added: New WPSCORE_Exception class
* Updated: Minimal PHP version 5.6.20 compatibiliy
* Fixed: Header already sends issue on plugin activation/deactivation
* Fixed: PHP Warning caused by WordPress 5.3
* Fixed: PHP Warning on product connexion
* Fixed: WP-Script Logs loading issue
* Fixed: Minor bugs

= 1.3.8 = Released on 2019-08-27
* Added: Wordfence compatibilty on ajax requests for all WP-Script products
* Added: Visual improvements on Activate / Deactivate buttons
* Updated: Update notification for plugins and themes is now visible only when the current version is lower (no more different) than the latest
* Fixed: Use gmdate() instead of date() to prevent durations issues on some servers configuration
* Fixed: Visuals bug on the dashboard page
* Fixed: Curl settings in Xbox options framework that prevented Niches to be activated with Retrotube in some cases
* Fixed: Warning Req. icon that wasn't displayed when all required PHP elements are not installed

= 1.3.7 = Released on 2019-07-26
* Added: New plugin "WPS Disclaimer" compatibility
* Fixed: Minor bugs

= 1.3.6 = Released on 2019-06-26
* Updated: Niches displaying in theme options

= 1.3.5 = Released on 2019-06-14
* Added: New niches import system for themes

= 1.3.4 = Released on 2019-06-12
* Fixed: default options on plugins activation
* Fixed: minor bugs

= 1.3.3 = Released on 2019-06-10
* Updated: CSS style
* Fixed: "The site is experiencing technical difficulties" issue

= 1.3.2 = Released on 2019-06-05
* Fixed: Warnings on plugin activation with some PHP versions

= 1.3.1 = Released on 2019-05-22
* Updated: Plugin Updater Class methods to be able to upgrade future versions of WP-Script plugins

= 1.3.0 = Released on 2019-05-10
* Updated: New look to stick to the new WP-Script.com design
* Updated: Vue.js version to v2.6.10
* Updated: Javascript code refactored
* Updated: CSS refactored to use the BEM methodology
* Updated: CSS splitting for faster loading
* Fixed: Products options that didn't work on localhost

= 1.2.9 = Released on 2019-03-04
* Updated: Vue.js version to v2.6.2
* Fixed: Options pages that don't load when domain path contains "themes" or "plugins" strings (extremely rare)
* Fixed: All Bootstrap JS loading collisions that could provide some issues
* Fixed: Xbox library to be 100% compatible with PHP 7.0

= 1.2.8 = Released on 2019-01-29
* Updated: Vue.js version to v2.5.21
* Fixed: Minor bugs

= 1.2.7 = Released on 2018-11-28
* Updated: Code updated to manage more than 10 sub-menus and prepare the future
* Fixed: Minor bugs

= 1.2.6 = Released on 2018-11-15
* Fixed: Gutenberg lodash.js collision with WP-Script Core lodash.js that prevented to download a logo in the theme options
* Fixed: Minor bugs

= 1.2.5 = Released on 2018-10-29
* Added: WP-Script GOLD manager box and features
* Updated: Webm video format compatibility for themes video information metabox
* Fixed: Products update links fixed on the Theme Options page

= 1.2.4 = Released on 2018-09-28
* Updated: Products update links removed from the notice in the dashboard page. To update a product, just click on the Update green buttons in the updatable products

= 1.2.3 = Released on 2018-08-03
* Updated: Better error detection with some servers configuration when saving license key or creating an account

= 1.2.2 = Released on 2018-08-01
* Fixed: Products installation/update issues with some servers configuration

= 1.2.1 = Released on 2018-07-04
* Updated: Theme options compatibility
* Fixed: Minor bugs

= 1.2.0 = Released on 2018-06-27
* Fixed: API calls errors when SERVER_NAME is not detected
* Fixed: HTTP / HTTPS server misconfiguration that can prevent assets (js/css) to be loaded
* Fixed: Minor bugs

= 1.1.9 = Released on 2018-06-15
* Fixed: Saving options that doesn't work in some cases
* Fixed: Minor bugs

= 1.1.8 = Released on 2018-06-11
* Fixed: cUrl errors
* Fixed: missing data in the dashboard in some cases after updating the Core
* Fixed: Minor bugs

= 1.1.7 = Released on 2018-06-08
* Updated: cUrl > v7.34.0 requirement doesn't block products anymore if not installed
* Fixed: Modalbox position issue when clicking on a button in the Tools options of WP-Script themes
* Fixed: Minor bugs

= 1.1.6 = Released on 2018-06-06
* Added: cUrl and cUrl > v7.34.0 requirements detection, preventing random issues
* Fixed: SERVER_ADDR Issues for local servers
* Fixed: Minor bugs

= 1.1.5 = Released on 2018-05-25
* Fixed: HTTP / HTTPS server misconfiguration that can prevent the Core to work properly
* Fixed: Minor bugs

= 1.1.4 = Released on 2018-05-07
* Added: Message in a modal box when there is a server error while installing/updating a product
* Fixed: All products reset button in options tab that didn't work

= 1.1.3 = Released on 2018-04-13
* Updated: Product activation is no longer possible if all required PHP elements are not installed. This prevents products side effects
* Updated: Product updates message and links (Update link redirects to the dashboard | Changelog link redirects to wp-script.com changelog page)
* Fixed: "Fatal error: Class 'SimpleXMLElement' not found" on some products activation
* Fixed: PHP notices when WP_DEBUG is activated
* Fixed: Minor bugs

= 1.1.2 = Released on 2018-04-09
* Added: Product name column in logs to filter logs by product
* Added: Link to product details on products images in dashboard
* Updated: WP-Script admin pages logo
* Updated: WP-Script menu logo
* Updated: All WP-Script plugins tabs are now collapsed in one tab with sub menus
* Fixed: Dropdown options that didn't work anymore because of bootstrap conflict
* Fixed: Minor bugs

= 1.1.1 = Released on 2018-03-20
* Added: Namespace has been added to Bootstrap to prevent conflicts with other plugins
* Updated: Compatibility with themes and plugins new versions
* Fixed: Google Font in Options pages are now loaded over HTTPS

= 1.1.0 = Released on 2018-02-28
* Fixed: API calls errors when SERVER_NAME is empty
* Fixed: Minor bugs

= 1.0.9 = Released on 2018-02-14
* Fixed: Empty thumbnail in the Video Information metabox

= 1.0.8 = Released on 2018-01-16
* Updated: Improvement of the video preview under the video URL field in the Video Information metabox. Displays now videos from YouTube, Google Drive and the most popular adult tubes. The old version displayed only MP4 videos.
* Fixed: Minor bugs

= 1.0.7 = Released on 2017-12-13
* Fixed: Error logs removed

= 1.0.6 = Released on 2017-12-05
* Fixed: Loading submenu issue

= 1.0.5 = Released on 2017-12-02
* Fixed: Thumbnails displaying issue in admin posts

= 1.0.4 = Released on 2017-12-01
* Added: Prevent any third party plugins scripts and css conflict on WP-Script pages
* Fixed: Displaying issues with some WP-Script themes options
* Fixed: Minor bugs

= 1.0.3 = Released on 2017-11-21
* Fixed: Fatal error when activating wp-script core on PHP < 3.5.0
* Fixed: Fatal error when activating Retro Tube Theme manually and wp-script core is not installed

= 1.0.2 = Released on 2017-11-13
* Fixed: Admin displaying issue when using Cloudflare or CDN service
* Fixed: Minor bugs

= 1.1. = Released on 2017-11-08
* Fixed: Core Auto-update issue (please replace WP-Script Core Plugin 1.0.0 by 1.1. manualy)
* Fixed: Core Upload issue when PHP allowed memory size si too small (<2MB)
* Fixed: RetroTube Theme installation / activation issues
* Fixed: Minor bugs

= 1.0.0 = Released on 2017-11-02
* First release
