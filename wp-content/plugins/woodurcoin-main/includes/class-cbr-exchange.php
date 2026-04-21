<?php
/**
 * A class for get currencies exchange rates from CBR
 *
 * @since      1.0.0
 * @package    Woodurcoin
 * @subpackage Woodurcoin/includes
 * @author     granvik
 * @class      CbrExchange
 */

class CbrExchange
{
    private $cbrSrc;

    public function __construct()
    {
        $this->cbrSrc = 'http://www.cbr.ru/scripts/XML_daily.asp';
    }

    public function getRate($fromCurrencyId, $toCurrencyId)
    {
        $pair = $fromCurrencyId . '/' . $toCurrencyId;
        $rate = wp_cache_get($pair, 'exchangeRates');
        if (0 == $rate) {
            $ratesRub = $this->fetchCbrRates();
            if ($fromCurrencyId == 'RUB') {
                $rate = 1 / $ratesRub[$toCurrencyId];
            } elseif ($toCurrencyId == 'RUB') {
                $rate = $ratesRub[$fromCurrencyId];
            } else {
                $rate = $ratesRub[$fromCurrencyId] / $ratesRub[$toCurrencyId];
            }
            wp_cache_set($pair, $rate, 'exchangeRates', 3600);
        }
        return $rate;
    }

    public function fetchCbrRates()
    {
        $response = wp_remote_get($this->cbrSrc);
        if (!$xml = simplexml_load_string(wp_remote_retrieve_body($response))) {
            return false;
        }
        $ratesRub = [];
        foreach ($xml->Valute as $valute) {
            $ratesRub[(string)$valute->CharCode] = ((float)str_replace(',', '.', $valute->Value)) / (float)$valute->Nominal;
            $ratesRub[1] = 1;
        }
        return $ratesRub;
    }

}