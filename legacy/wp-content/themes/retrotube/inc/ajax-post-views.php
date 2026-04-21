<?php
function wpst_set_post_views() {
    $nonce = $_POST['nonce'];
    if ( ! wp_verify_nonce( $nonce, 'ajax-nonce' ) )
      die ( 'Busted!');

    if( ! isset($_POST['post_id'] ) ){
      die ( 'post id required!');
    }

    $postID = $_POST['post_id'];

    $count_key = 'post_views_count';
    $count = get_post_meta($postID, $count_key, true);
    if($count == ''){
      $count = 0;
      delete_post_meta($postID, $count_key);
      add_post_meta($postID, $count_key, '0');
    }else{
      $count++;
      update_post_meta($postID, $count_key, $count);
    }

    wp_send_json(array('views' => $count));
    wp_die();
}
add_action('wp_ajax_nopriv_post-views', 'wpst_set_post_views');
add_action('wp_ajax_post-views', 'wpst_set_post_views');