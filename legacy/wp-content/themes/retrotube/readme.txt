=== RetroTube ===

== Changelog ==

= 1.3.9 = 2020-02-13
* Fixed: Footer logo displaying issue

= 1.3.8 = 2020-02-07
* Added: Limit to display up to 1000 tags on tags page to prevent memory issues
* Fixed: Missing field: thumbnailUrl issue in Google indexing
* Fixed: Use gmdate() instead of date() to prevent durations issues on some servers configuration

= 1.3.7 = 2019-08-09
* Added: New niche "MILF" added to Niches section in the theme options
* Fixed: Extra double quote before "First" text in the pagination

= 1.3.6 = 2019-07-19
* Added: New niche "Hentai" added to Niches section in the theme options

= 1.3.5 = 2019-07-17
* Fixed: Warnings and errors with very old versions of PHP (but please, update your PHP version)
* Fixed: bxSlider JS error when activating the Caroussel feature without adding videos to it

= 1.3.4 = 2019-07-01
* Added: New niche "College" added to Niches section in the theme options

= 1.3.3 = 2019-06-26
* Added: New niche "Lesbian" added to Niches section in the theme options
* Added: Resolution switcher compatibility with FluidPlayer and WPS Player

= 1.3.2 = 2019-06-20
* Added: New niche "Trans" added to Niches section in the theme options

= 1.3.1 = 2019-06-17
* Added: New niche "LiveXCams" added to Niches section in the theme options

= 1.3.0 = 2019-06-14
* Added: New niche "FILF" added to Niches section in the theme options
* Added: New theme option section named "Niches" which allows you to change the look of your site in one click
* Added: New option named "Rendering" with 2 choices "Flat" or "Gradient"
* Fixed: Photo gallery on blog posts and pages displaying

= 1.2.9 = 2019-05-14
* Added: New option to choose the categories thumbnail quality
* Added: New option to display or not the sidebar on categories template page
* Added: New option to choose the number of categories per row
* Added: New option to choose the number of videos per category page
* Added: New option "background size" for the custom background section
* Fixed: Video-functions.php file to be child theme ready
* Fixed: "A non-numerical value encountered" warnings with php 7.3
* Fixed: "Warning: count(): Parameter must be an array or an object that implements Countable" warnings with php 7.3

= 1.2.8 = 2019-04-29
* Fixed: Close ad button when no ad displaying issue
* Fixed: PHP "Fatal error: Can't use function return value in write context" with some old PHP versions

= 1.2.7 = 2019-04-26
* Fixed: bxSlider click event issue on Chrome
* Fixed: Number of categories per page option
* Fixed: In-video banner display when WPS player plugin activated

= 1.2.6 = 2019-04-24
* Added: New layout option "Boxed" or "Full Width"
* Added: Option to display or not your logo in the footer
* Added: Alt tag in the footer logo image
* Added: New option to display Title and Description at the top or the bottom of the homepage
* Added: New option to display H1 title on the homepage to improve SEO
* Added: New option to display the tag description at the top or the bottom of the tag page
* Updated: Possibility to display photos and blog categories and tags directly from the menu items selector
* Updated: Login link in the comment section when users have to be logged to post a comment
* Fixed: Thumbnails rotation (the first image was bypass, the latest was displayed two times)
* Fixed: Actor name in the breadcrumb
* Fixed: Popular videos filter
* Fixed: Likes counter display that could go back to the line
* Fixed: "Uncaught (in promise) DOMException" console error when hovering videos trailers too fast in Google Chrome

= 1.2.5 = 2019-01-18
* Updated: New WordPress editor for Blog and Photos posts

= 1.2.4 = 2019-01-09
* Added: 4k resolution field in Video Information metabox
* Fixed: Menu button position on mobile device
* Fixed: Some banners displayed over the open mobile menu

= 1.2.3 = 2018-12-18
* Fixed: Actors taxonomy not showed in video post admin since WordPress 5 release

= 1.2.2 = 2018-12-05
* Added: Option in Membership section to display or not the admin bar for logged in users
* Added: Option in Mobile section (Code tab) to add scripts only for mobile device
* Added: New "Code" tab option in Mobile section 
* Updated: get_stylesheet_directory_uri() function replaced by get_template_directory_uri() for child theme compatibility
* Fixed: Breadcrumbs displaying
* Fixed: Thumb link didn't work on mobile in some cases
* Fixed: Logo and menu position on mobile
* Fixed: Before play advertising displaying when embed code was added directly in the description field
* Fixed: Minor bugs

= 1.2.1 = 2018-11-15
* Updated: Menu section position on mobile device
* Updated: Top bar elements position on mobile device
* Fixed: Other images than gallery images, like banners for example, opened in lightbox in photos gallery pages
* Fixed: Fluid Player on pause ads that didn't work in JavaScript
* Fixed: Fluid Player on start ads that didn't close when playing the video
* Fixed: Fluid Player console error "Cannot read property 'setAttribute' of null"
* Fixed: Minor bugs

= 1.2.0 = 2018-11-06
* Added: Thumbnail image in RSS feed
* Fixed: JavaScript versioning

= 1.1.9 = 2018-11-02
* Fixed: In-video advertising location size in mobile version
* Fixed: YouTube embed player generation from YouTube video URL

= 1.1.8 = 2018-10-31
* Fixed: Close over video advertising issue with iframe players

= 1.1.7 = 2018-10-30
* Added: Mid-roll in-stream ad with timer in the "Video Player" theme option section. It plays a video advertising in the middle of the video automatically (you can set a timer when you want the advertising starts. For example 50%.)
* Added: Pre-roll in-stream ad in the "Video Player" theme option section. It plays a video advertising with a skip ad button at the beginning
* Added: Close and play button at the bottom of the banners over the video which automatically plays the video
* Added: On pause advertising zone 1 & 2 in the "Video Player" theme option section. These banners are displayed over the video player when the user pauses the video
* Added: Before play advertising zone 1 & 2 in the "Video Player" theme option section. These banners are displayed over the video player when the user arrives on the page
* Added: New logo options in the "Video Player" theme option section (with logo position, margin, opacity and grayscale features)
* Added: Playback Speed option in the "Video Player" theme option section (Add a new control bar option to allow users to play video at different speeds)
* Added: New Autoplay option in the "Video Player" theme option section (The video plays automatically)
* Added: New theme option menu named "Video Player"
* Added: New Video Resolutions fields (240p, 360p, 480p, 720p and 1080p) in the RetroTube - Video Information metabox
* Added: Listing of random videos in 404 or nothing found result search pages
* Updated: VideoJS video player replaced by FluidPlayer
* Updated: Webm format compatibility for video trailers
* Updated: Text for SEO option moved to homepage only to improve SEO (the option is now in Theme Options > Content > Homepage tab)
* Fixed: Minor bugs

= 1.1.6 = 2018-09-20
* Added: Number of photos per gallery in archive photos page
* Added: Photos loading message with counter
* Updated: Improvement of the waterfall effect loading
* Updated: Improvement of the photos archive displaying

= 1.1.5 = 2018-09-19
* Added: Improvement of the photos gallery displaying with waterfall effect
* Added: Lazy load on photos
* Added: Easy navigation between each photos
* Fixed: Minor bugs

= 1.1.4 = 2018-09-10
* Added: Video trailer as preview on mouse hover in your video listing
* Added: Video trailer URL field in the RetroTube - Video Information metabox
* Added: Preview of the video trailer in the RetroTube - Video Information metabox
* Added: New section "Blog" with possibility to add articles with categories and tags
* Added: New section "Photos" with possibility to add photos and create galleries
* Added: Lightbox system to open photos from a gallery
* Updated: "Posts" admin menu changed to "Videos" (for a better understanding)

= 1.1.3 = 2018-07-18
* Fixed: 404 pages issue

= 1.1.2 = 2018-07-04
* Added: Pagination for actors list
* Added: Full Width page template
* Added: Possibility to edit views and likes for each post in the Video Information metabox
* Added: Author, title and description video itemprop infos
* Added: Tags and actors in video submission form for users
* Added: New option to choose Aspect ratios of thumbnails (16/9 or 4/3)
* Added: New option to choose Main thumbnail quality (basic, normal or fine)
* Added: New option to choose the position of category description (top or bottom of the page)
* Added: New option to set the same link for every tracking buttons in video pages
* Added: New option to choose the "Actors" label in video pages
* Added: New option to add text in the footer to improve SEO
* Added: New option to choose the number of actors per page
* Fixed: Popular videos list display issue when no rated videos
* Fixed: Loading of social metas outside the video pages
* Fixed: Video information metabox displayed in page edition
* Fixed: Minor bugs

= 1.1.1 = 2018-04-24
* Added: Alt and Title tags with site name on logo image to improve SEO
* Updated: All advertising locations are now compatible with Ad Rotate plugin shortcodes
* Fixed: Space issue between tags
* Fixed: PHP Warnings generated by the Rates function
* Fixed: Preventing visitors to vote multiple times on videos

= 1.1.0 = 2018-04-09
* Added: Option to choose number of videos per page on mobile device
* Added: HD video switch option in the RetroTube - Video information metabox. Displays a HD label over the thumbnail
* Updated: Names of advertising block class to avoid AdBroker issue
* Updated: Advertising locations are now compatible with Ad Rotate plugin shortcodes
* Updated: Improved display of blocks on video pages in mobile mode
* Fixed: Opening featured videos displayed from the carousel on Firefox
* Fixed: Login/Register popup display issue with navigation
* Fixed: CSS version that didn't change preventing to see CSS changes when updating the theme

= 1.0.9 = 2018-03-27
* Fixed: Post format query issue
* Fixed: In-video width banner display issue
* Fixed: Views counting with some cache plugins

= 1.0.8 = 2018-03-20
* Added: Possibility to upload an image for actors
* Added: Integration of tags and actors fields in the frontend Video Submission form
* Added: Blog template page which allow you to create a separate blog page with "standard" posts
* Added: Create Blog page button in the theme options tools
* Added: Video preview for embed code section in the video information metabox (post admin)
* Added: Mobile section in the theme options with 2 tabs: General and Advertising
* Added: Option to choose the number of videos per row on mobile
* Added: Option to choose if you want to disable or keep widgets on your homepage on mobile
* Added: Filters in tag and search page results
* Added: Instagram social share profile option in the top bar
* Updated: Duration field changed to HH MM SS in the video information metabox (post admin)
* Updated: Actors template page with images
* Updated: Menu on desktop and mobile improvement
* Updated: Unique banner under the video player displayed on mobile devices too
* Updated: Design improvement of the social buttons in the top bar
* Fixed: Twitter sharing with image, title and description
* Fixed: Facebook sharing with image, title and description
* Fixed: Slogan not visible when logo too big
* Fixed: Filters and pagination issue
* Fixed: Views and likes compatible with cache plugins
* Fixed: Sidebar displaying issue on mobile
* Fixed: Footer menu displaying
* Fixed: Description content displaying on mobile
* Fixed: Share buttons displaying on mobile
* Fixed: Minor bugs

= 1.0.7 = 2018-01-16
* Added: Possibility to display a unique banner under the video player for each post
* Added: Option to enable or not related videos
* Added: Option to set the number of related videos
* Added: "Show more related videos" button displayed under the related videos listing
* Added: Possibility to set an image for each category
* Added: Option to choose if you want to display or not a comments section in your single video pages.
* Added: Option to choose if you want to display or not the carousel of featured videos on mobile devices.
* Added: Option to choose if you want to display or not the sidebar on mobile devices.
* Added: Footer menu
* Updated: Custom CSS option removed. Compatibility with the additional CSS option in the WordPress customizer
* Updated: Translation pot file expressions
* Updated: Video URL preview in the Video Information metabox with YouTube, Google Drive and the most popular adult tubes
* Fixed: Close button on in-video advertising which passed behind the banners
* Fixed: Submit a video form redirection issue from some server
* Fixed: Minor bugs

= 1.0.6 = 2017-12-02
* Fixed: Fatal error on single video pages with some PHP versions

= 1.0.5 = 2017-12-01
* Added: Option to enable / disable thumbnails rotation
* Added: Possibility to display your Tumblr social profile link in the topbar
* Updated: Improvement of the read more feature for truncate descriptions
* Updated: Lazy load feature
* Fixed: Thumbnails used for rotation saving during a manual post creation
* Fixed: Tracking URL button displaying issue in mobile version
* Fixed: Comments fields displaying in mobile version
* Fixed: In-video banners size
* Fixed: Minor bugs

= 1.0.4 = 2017-11-21
* Fixed: Inside video player advertising width display issue

= 1.0.3 = 2017-11-21
* Fixed: Pornhub, Redtube, Spankwire, Tube8, Xhamster, Xvideos and Youporn embed player displaying issue when the URL of the video was saved in Video URL field.
* Fixed: Minor bugs

= 1.0.2 = 2017-11-17
* Added: VK sharing button on single video pages
* Fixed: Fatal error on single video pages with some PHP versions
* Fixed: Issue with login / register system when "Anyone can register" option was disabled
* Fixed: Minor bugs

= 1.0.1 = 2017-11-08
* Fixed: Inside video player advertising display issue

= 1.0.0 = 2017-10-30
* Initial release