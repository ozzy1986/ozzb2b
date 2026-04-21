<?php 
	global $post;
	$thumb = get_post_meta($post->ID, 'thumb', true);
	$post_data = wpst_get_post_data($post->ID);
    $url_image = has_post_thumbnail() ? wp_get_attachment_url( get_post_thumbnail_id($post->ID)) : $thumb;
    $current_url = get_permalink( $post->ID );
    $current_title = $post_data->post_title;
    $current_desc = '';
    if( !empty($post_data->post_content) ){
        $current_desc = esc_html($post_data->post_content);
    }else{
        $current_desc = esc_html($current_title);
	}
?>

<!-- Meta Facebook -->
<meta property="fb:app_id" 			   content="966242223397117" />
<meta property="og:url"                content="<?php echo $current_url; ?>" />
<meta property="og:type"               content="article" />
<meta property="og:title"              content="<?php echo $current_title; ?>" />
<meta property="og:description"        content="<?php echo $current_desc; ?>" />
<meta property="og:image"              content="<?php echo $url_image; ?>" />
<meta property="og:image:width" 	   content="200" />
<meta property="og:image:height" 	   content="200" />

<!-- Meta Twitter -->
<meta name="twitter:card" content="summary">
<!--<meta name="twitter:site" content="@site_username">-->
<meta name="twitter:title" content="<?php echo $current_title; ?>">
<meta name="twitter:description" content="<?php echo $current_desc; ?>">
<!--<meta name="twitter:creator" content="@creator_username">-->
<meta name="twitter:image" content="<?php echo $url_image; ?>">
<!--<meta name="twitter:domain" content="YourDomain.com">-->