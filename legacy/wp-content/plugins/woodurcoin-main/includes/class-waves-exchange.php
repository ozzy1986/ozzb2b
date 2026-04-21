<?php
/**
 * A class for receiving and processing information from the waves.exchange about assets
 * and exchange rates (last)
 *
 * @since      1.0.0
 * @package    Woodurcoin
 * @subpackage Woodurcoin/includes
 * @author     granvik
 * @class      WavesExchange
 */

class WavesExchange
{
    private $orderBookSrc;
    private $assetDetailsSrc;
    private $assets;

    public function __construct()
    {
        $this->orderBookSrc = "https://matcher.waves.exchange/matcher/orderbook/";
        $this->assetDetailsSrc = "https://nodes.wavesnodes.com/assets/details/";
        $this->assets = [
            'WAVES' => [
                'assetId' => 'WAVES',
                'name' => 'WAVES',
                'decimals' => 8,
                'description' => 'WAVES'
            ],
            'DG2xFkPdDwKUoBkzGAhQtLpSGzfXLiCYPEzeKH2Ad24p' => [
                'assetId' => 'DG2xFkPdDwKUoBkzGAhQtLpSGzfXLiCYPEzeKH2Ad24p',
                'name' => 'USD-N',
                'decimals' => 6,
                'description' => 'Neutrino USD'
            ],
            'F1HoALyCDnvMbMxZcvWEVdtPXTY9BL9nbHnzSyjRLTt8' => [
                'assetId' => 'F1HoALyCDnvMbMxZcvWEVdtPXTY9BL9nbHnzSyjRLTt8',
                'name' => 'Durcoin',
                'decimals' => 2,
                'description' => 'SEC+Gram=Durcoin'
            ],
        ];
    }

    /**
     * @return false|float|int
     */
    public function getRate($fromAssetId, $toAssetId)
    {
        $pair = $fromAssetId . '/' . $toAssetId;
        $rate = wp_cache_get($pair, 'exchangeRates');

        if (0 == $rate) {
            if (empty($this->assets[$fromAssetId]['assetId'])) {
                $this->assets = $this->fetchAssetInfo($fromAssetId);
            }
            if (empty($this->assets[$toAssetId]['assetId'])) {
                $this->assets = $this->fetchAssetInfo($toAssetId);
            }
            $rate = 0;
            if (!empty($this->assets[$fromAssetId]['assetId']) && !empty($this->assets[$toAssetId]['assetId'])) {
                $rate = $this->fetchWavesRate($fromAssetId, $toAssetId);
            }
            wp_cache_set($pair, $rate, 'exchangeRates', 3600);
        }
        return $rate;
    }

    /**
     * @return false|float|int
     */
    public function fetchWavesRate($fromAssetId, $toAssetId)
    {
        $response = wp_remote_get($this->orderBookSrc . $fromAssetId . '/' . $toAssetId . '?depth=1');
        $json = wp_remote_retrieve_body($response);
        $obj = json_decode($json);
        if (!empty($obj->asks[0])) {
            return (float)$obj->asks[0]->price / (10 ** (8 + $this->assets[$fromAssetId]['decimals'] - $this->assets[$toAssetId]['decimals']));
        }
        $response = wp_remote_get($this->orderBookSrc . $fromAssetId . '/' . $toAssetId . '/status');
        $json = wp_remote_retrieve_body($response);
        $obj = json_decode($json);
        if (empty($obj->lastPrice)) {
            return false;
        } else {
            return (float)$obj->lastPrice / (10 ** (8 + $this->assets[$fromAssetId]['decimals'] - $this->assets[$toAssetId]['decimals']));
        }
    }

    /**
     * @return object|false
     */
    public function fetchAssetInfo($assetId)
    {
        $response = wp_remote_get($this->assetDetailsSrc . $assetId);
        $json = wp_remote_retrieve_body($response);
        $obj = json_decode($json);
        if (empty($obj->assetId)) {
            return false;
        } else {
            return $obj;
        }
    }
}