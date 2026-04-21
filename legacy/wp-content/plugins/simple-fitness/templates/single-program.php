<?php
/**
 * The template for displaying Program single posts
 */

if ( wp_is_block_theme() ) {

	?><!doctype html>
	<html <?php language_attributes(); ?>>
	<head>
		<meta charset="<?php bloginfo( 'charset' ); ?>">

		<?php wp_head(); ?>
	</head>

	<body <?php body_class(); ?>>
	<?php wp_body_open(); ?>
	<div class="wp-site-blocks">

    <?php
    //block_template_part('header');
    block_header_area(); // same as above
} else {
	get_header();
}


// Main content
$exercise_meta		= get_post_meta( $post->ID, 'program_exercise_meta_box', true );
$rest_after_meta	= get_post_meta( $post->ID, 'program_exercise_rest_after_meta_box', true );
$duration_meta		= get_post_meta( $post->ID, 'program_exercise_duration_meta_box', true );

// get existing exercises
$exercises = get_posts([
	'post__in'		=> $exercise_meta,
	'post_type'		=> 'exercise'
]);
//echo '<br>exercises:<pre>' . print_r( $exercises, true ) . '</pre><br>';
?>
<table>
	<tr>
		<th><?php _e( 'Упражнение', 'twentytwentytwo' ); ?></th>
		<th><?php _e( 'Отдых, секунды', 'twentytwentytwo' ); ?></th>
		<th colspan="2"><?php _e( 'Длительность, секунды', 'twentytwentytwo' ); ?></th>
	</tr>
<?php
for ( $i = 0; $i < count( $exercises ); $i++ ) {
	?>
	<tr>
		<td><?php echo $exercises[ $i ]->post_title; ?></td>
		<td><?php echo $rest_after_meta[ $i ]; ?></td>
		<td><?php echo $duration_meta[ $i ]; ?></td>
	</tr>
	<?php
}
?>
</table>


<?php
if ( wp_is_block_theme() ) {
    block_template_part('footer');
    ?>
    </div>
	<?php wp_footer(); ?>

	</body>
	</html>
	<?php
} else {
	get_footer();
}
