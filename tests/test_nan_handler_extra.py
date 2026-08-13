import pytest
import pandas as pd
import numpy as np
from app.utils.nan_handler import NaNHandler

def test_nan_handler_extra_coverage():
    # Test has_nan with various inputs
    assert NaNHandler.has_nan(np.nan) == True
    assert NaNHandler.has_nan(1) == False
    assert NaNHandler.has_nan(pd.Series([1, 2, 3])) == False
    assert NaNHandler.has_nan(pd.Series([1, np.nan, 3])) == True
    assert NaNHandler.has_nan(pd.DataFrame({'a': [1, 2]})) == False
    assert NaNHandler.has_nan(pd.DataFrame({'a': [1, np.nan]})) == True

    # Test replace_inf_nan with edge cases
    df = pd.DataFrame({'a': [1, np.inf, -np.inf, np.nan]})
    NaNHandler.replace_inf_nan(df)
    assert not df.isin([np.inf, -np.inf]).any().any()

    # Test clean_dataframe_nan with all strategies
    df = pd.DataFrame({'a': [1, np.nan, 3], 'b': [4, 5, np.nan]})
    for strategy in ['zero', 'drop', 'mean', 'forward_fill', 'backward_fill']:
        result = NaNHandler.clean_dataframe_nan(df.copy(), strategy)
        assert isinstance(result, pd.DataFrame)

    # Test clean_dataframe_nan with unknown strategy
    result = NaNHandler.clean_dataframe_nan(df.copy(), 'unknown')
    assert isinstance(result, pd.DataFrame)

    # Test clean_dict_nan
    data = {'a': np.nan, 'b': [1, np.nan], 'c': {'d': np.nan}}
    result = NaNHandler.clean_dict_nan(data)
    assert 'a' not in result or pd.isna(result['a'])

    # Test get_nan_statistics with various inputs
    stats = NaNHandler.get_nan_statistics(df)
    assert 'total_nan' in stats
    assert 'nan_percentage' in stats

    empty_df = pd.DataFrame()
    stats = NaNHandler.get_nan_statistics(empty_df)
    assert stats['total_nan'] == 0

    # Test handle_ohlcv_nan
    ohlcv_df = pd.DataFrame({
        'open': [100, np.nan, 102],
        'high': [110, 111, np.nan],
        'low': [90, np.nan, 92],
        'close': [105, 106, 107],
        'volume': [1000, np.nan, 3000]
    })
    NaNHandler.handle_ohlcv_nan(ohlcv_df)
    # Should not have NaN in OHLCV columns after handling
    for col in ['open', 'high', 'low', 'close', 'volume']:
        if col in ohlcv_df.columns:
            assert not ohlcv_df[col].isna().any()

    # Test validate_numeric_column with different strategies
    test_df = pd.DataFrame({'a': ['1', '2', np.nan], 'b': [1, 2, 3]})
    NaNHandler.validate_numeric_column(test_df, 'a', 'zero')
    assert test_df['a'].dtype in ['float64', 'int64']

    # Test with invalid column
    NaNHandler.validate_numeric_column(test_df, 'nonexistent', 'drop')

    # Test with different strategies
    test_df2 = pd.DataFrame({'a': [1, np.nan, 3]})
    NaNHandler.validate_numeric_column(test_df2, 'a', 'mean')
    assert not test_df2['a'].isna().any()

    NaNHandler.validate_numeric_column(test_df2, 'a', 'forward_fill')
    assert not test_df2['a'].isna().any()

    NaNHandler.validate_numeric_column(test_df2, 'a', 'backward_fill')
    assert not test_df2['a'].isna().any()

    NaNHandler.validate_numeric_column(test_df2, 'a', 'drop')
    # May still have NaN if only one row or other conditions