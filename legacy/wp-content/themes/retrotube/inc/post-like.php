<?php
function wpst_hasAlreadyVoted($post_id) {
	$timebeforerevote = 86400;//60sec * 60min * 24h
	$ip = $_SERVER['REMOTE_ADDR'];
	if(!$ip) return false;

	$voted_IPs = get_post_meta($post_id, "voted_IP", true);
	if( !is_array($voted_IPs) )
		$voted_IPs = array();

	if(in_array($ip, array_keys($voted_IPs))){
		$time = $voted_IPs[$ip];
		$now = time();
		if(round(($now - $time) / 60) > $timebeforerevote)
			return false;
		return true;
	}
	return false;
}
function wpst_getPostLikeLink($post_id){
	$output = '<span class="post-like">';
	if(wpst_hasAlreadyVoted($post_id)){
		$output .= '';
	}else{
		$output .= '<a href="#" data-post_id="'.$post_id.'" data-post_like="like"><span class="like" title="' . esc_html__('I like this', 'wpst') . '"><span id="more"><i class="fa fa-thumbs-up"></i> <span class="grey-link">' . esc_html__('Like', 'wpst') . '</span></span></a>
		<a href="#" data-post_id="'.$post_id.'" data-post_like="dislike">
			<span title="' . esc_html__('I dislike this', 'wpst') . '" class="qtip dislike"><span id="less"><i class="fa fa-thumbs-down fa-flip-horizontal"></i></span></span>
		</a>';
		$output .= '</span>';
	}
	return $output;
}
function wpst_getPostLikeRate( $post_id ){
	$like_count     = intval(get_post_meta($post_id, "likes_count", true));
	$dislike_count  = intval(get_post_meta($post_id, "dislikes_count", true));

	$total_count    =  $like_count + $dislike_count;
	if($total_count > 0)
		return ceil($like_count / $total_count * 100) . '%';
	else
		return false;
}
function wpst_getItemPostLikeRate( $post_id ){
	if( wpst_getPostLikeRate($post_id) !== false )
		return wpst_getPostLikeRate($post_id) . '%';
	else
		return false;
}