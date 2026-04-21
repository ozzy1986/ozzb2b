<?php
function wpst_get_async_post_data() {
    $nonce = $_POST['nonce'];

    if ( ! wp_verify_nonce( $nonce, 'ajax-nonce' ) )
        die ( 'Busted!');
    
    if(isset($_POST['post_id'])){
        wp_send_json(
            array(
                'views'     => (int) wpst_getPostViews($_POST['post_id']),
                'likes'     => (int) get_post_meta($_POST['post_id'], 'likes_count', true),
                'dislikes'  => (int) get_post_meta($_POST['post_id'], 'dislikes_count', true ),
                'rating'    => wpst_getPostLikeRate($_POST['post_id'])
            )
        );
    }else{
        return false;
    }
    wp_die();
}

add_action('wp_ajax_nopriv_get-post-data', 'wpst_get_async_post_data');
add_action('wp_ajax_get-post-data', 'wpst_get_async_post_data');