"""
🧠 Deep Learning Anomaly Detection — Advanced Neural Genome Sequencing

State-of-the-art deep learning models for financial anomaly detection
inspired by advanced genomic sequencing techniques. Multiple neural
architectures work together like a sophisticated genetic analysis lab.

From single cells to complex organisms. From simple patterns to market regimes.
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging
from dataclasses import dataclass, field
import warnings
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

from ..core.base_layers import BaseDetector, DetectionResult
from ..core.genome import FinancialGenome

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)


@dataclass
class DeepLearningConfig:
    """
    🔬 Deep Learning Detection Configuration
    
    Advanced configuration for neural network-based anomaly detection
    with multiple architectures and ensemble capabilities.
    """
    # Model architecture settings
    lstm_hidden_size: int = 128
    lstm_num_layers: int = 2
    transformer_d_model: int = 256
    transformer_n_heads: int = 8
    transformer_n_layers: int = 6
    cnn_channels: List[int] = field(default_factory=lambda: [32, 64, 128])

    # Training parameters
    sequence_length: int = 60  # 60 days lookback
    batch_size: int = 32
    learning_rate: float = 0.001
    num_epochs: int = 100
    early_stopping_patience: int = 10
    dropout_rate: float = 0.2

    # Anomaly detection settings
    anomaly_threshold: float = 0.95  # 95th percentile
    ensemble_voting: str = "soft"  # "soft" or "hard"
    enable_uncertainty_quantification: bool = True

    # Data preprocessing
    normalize_features: bool = True
    use_technical_indicators: bool = True
    include_volume_features: bool = True


class LSTMAutoencoderDetector(nn.Module):
    """
    🧬 LSTM Autoencoder for Time Series Anomaly Detection
    
    Like analyzing DNA sequences for mutations, this model learns
    normal financial patterns and identifies deviations.
    """

    def __init__(self,
                 input_size: int,
                 hidden_size: int = 128,
                 num_layers: int = 2,
                 dropout: float = 0.2):
        super(LSTMAutoencoderDetector, self).__init__()

        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        # Encoder
        self.encoder_lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )

        # Bottleneck
        self.bottleneck = nn.Linear(hidden_size, hidden_size // 2)

        # Decoder
        self.decoder_lstm = nn.LSTM(
            input_size=hidden_size // 2,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )

        self.output_layer = nn.Linear(hidden_size, input_size)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        batch_size, seq_len, _ = x.size()

        # Encode
        encoded, (h_n, c_n) = self.encoder_lstm(x)

        # Bottleneck - use last hidden state
        compressed = self.bottleneck(encoded[:, -1, :])  # [batch_size, hidden_size//2]
        compressed = self.dropout(compressed)

        # Prepare for decoder
        decoder_input = compressed.unsqueeze(1).repeat(1, seq_len, 1)  # [batch_size, seq_len, hidden_size//2]

        # Decode
        decoded, _ = self.decoder_lstm(decoder_input)
        output = self.output_layer(decoded)

        return output, compressed


class TransformerAnomalyDetector(nn.Module):
    """
    🔄 Transformer-based Anomaly Detection
    
    Uses self-attention mechanisms to understand complex temporal
    dependencies in financial data, like studying gene expression patterns.
    """

    def __init__(self,
                 input_size: int,
                 d_model: int = 256,
                 n_heads: int = 8,
                 n_layers: int = 6,
                 dropout: float = 0.2):
        super(TransformerAnomalyDetector, self).__init__()

        self.input_size = input_size
        self.d_model = d_model

        # Input projection
        self.input_projection = nn.Linear(input_size, d_model)

        # Positional encoding
        self.positional_encoding = PositionalEncoding(d_model, dropout)

        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=n_heads,
            dim_feedforward=d_model * 4,
            dropout=dropout,
            activation='gelu',
            batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)

        # Output layers
        self.output_projection = nn.Linear(d_model, input_size)
        self.anomaly_score_head = nn.Linear(d_model, 1)

    def forward(self, x):
        # Project input to model dimension
        x_proj = self.input_projection(x)  # [batch_size, seq_len, d_model]

        # Add positional encoding
        x_pos = self.positional_encoding(x_proj)

        # Transform
        transformer_output = self.transformer_encoder(x_pos)  # [batch_size, seq_len, d_model]

        # Reconstruction
        reconstruction = self.output_projection(transformer_output)

        # Anomaly score (using mean pooling over sequence)
        pooled = torch.mean(transformer_output, dim=1)  # [batch_size, d_model]
        anomaly_score = torch.sigmoid(self.anomaly_score_head(pooled))  # [batch_size, 1]

        return reconstruction, anomaly_score


class PositionalEncoding(nn.Module):
    """Positional encoding for Transformer."""

    def __init__(self, d_model: int, dropout: float = 0.1, max_len: int = 5000):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)

        position = torch.arange(max_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2) * (-np.log(10000.0) / d_model))
        pe = torch.zeros(max_len, 1, d_model)
        pe[:, 0, 0::2] = torch.sin(position * div_term)
        pe[:, 0, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe)

    def forward(self, x):
        x = x + self.pe[:x.size(1)].transpose(0, 1)
        return self.dropout(x)


class CNNFeatureExtractor(nn.Module):
    """
    🖼️ CNN Feature Extractor for Financial Patterns
    
    Extracts local patterns from financial time series using
    convolutional layers, like identifying genetic motifs.
    """

    def __init__(self,
                 input_channels: int = 1,
                 channels: List[int] = [32, 64, 128],
                 kernel_sizes: List[int] = [3, 5, 7],
                 dropout: float = 0.2):
        super(CNNFeatureExtractor, self).__init__()

        self.conv_layers = nn.ModuleList()

        # Multi-scale convolutions
        for i, (out_channels, kernel_size) in enumerate(zip(channels, kernel_sizes)):
            in_channels = input_channels if i == 0 else channels[i-1]

            conv_block = nn.Sequential(
                nn.Conv1d(in_channels, out_channels, kernel_size, padding=kernel_size//2),
                nn.BatchNorm1d(out_channels),
                nn.ReLU(),
                nn.MaxPool1d(2),
                nn.Dropout(dropout)
            )
            self.conv_layers.append(conv_block)

        # Global average pooling
        self.global_pool = nn.AdaptiveAvgPool1d(1)

        # Feature dimension
        self.feature_dim = sum(channels)

    def forward(self, x):
        # x shape: [batch_size, seq_len, features]
        # Reshape for CNN: [batch_size, 1, seq_len]
        if len(x.shape) == 3:
            x = x.transpose(1, 2)  # [batch_size, features, seq_len]

        features = []

        for conv_layer in self.conv_layers:
            x = conv_layer(x)
            # Global pooling for this scale
            pooled = self.global_pool(x).squeeze(-1)  # [batch_size, channels]
            features.append(pooled)

        # Concatenate multi-scale features
        combined_features = torch.cat(features, dim=1)  # [batch_size, total_channels]

        return combined_features


class EnsembleAnomalyDetector(nn.Module):
    """
    🎭 Ensemble Anomaly Detection System
    
    Combines multiple detection models for robust anomaly identification,
    like using multiple genetic testing methods for accurate diagnosis.
    """

    def __init__(self,
                 input_size: int,
                 config: DeepLearningConfig):
        super(EnsembleAnomalyDetector, self).__init__()

        self.config = config

        # LSTM Autoencoder
        self.lstm_detector = LSTMAutoencoderDetector(
            input_size=input_size,
            hidden_size=config.lstm_hidden_size,
            num_layers=config.lstm_num_layers,
            dropout=config.dropout_rate
        )

        # Transformer
        self.transformer_detector = TransformerAnomalyDetector(
            input_size=input_size,
            d_model=config.transformer_d_model,
            n_heads=config.transformer_n_heads,
            n_layers=config.transformer_n_layers,
            dropout=config.dropout_rate
        )

        # CNN Feature Extractor + Classifier
        self.cnn_extractor = CNNFeatureExtractor(
            input_channels=input_size,
            channels=config.cnn_channels,
            dropout=config.dropout_rate
        )

        self.cnn_classifier = nn.Sequential(
            nn.Linear(self.cnn_extractor.feature_dim, 256),
            nn.ReLU(),
            nn.Dropout(config.dropout_rate),
            nn.Linear(256, 1),
            nn.Sigmoid()
        )

        # Ensemble combination layer
        self.ensemble_combiner = nn.Sequential(
            nn.Linear(3, 64),  # 3 model outputs
            nn.ReLU(),
            nn.Dropout(config.dropout_rate),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        batch_size = x.size(0)

        # LSTM Autoencoder
        lstm_reconstruction, lstm_compressed = self.lstm_detector(x)
        lstm_mse = F.mse_loss(lstm_reconstruction, x, reduction='none')
        lstm_anomaly_score = torch.mean(lstm_mse.view(batch_size, -1), dim=1, keepdim=True)

        # Transformer
        transformer_reconstruction, transformer_score = self.transformer_detector(x)

        # CNN
        cnn_features = self.cnn_extractor(x)
        cnn_anomaly_score = self.cnn_classifier(cnn_features)

        # Combine scores
        if self.config.ensemble_voting == "soft":
            # Use ensemble combiner
            combined_scores = torch.cat([
                lstm_anomaly_score,
                transformer_score,
                cnn_anomaly_score
            ], dim=1)

            final_score = self.ensemble_combiner(combined_scores)
        else:
            # Hard voting (majority)
            threshold = 0.5
            votes = torch.cat([
                (lstm_anomaly_score > threshold).float(),
                (transformer_score > threshold).float(),
                (cnn_anomaly_score > threshold).float()
            ], dim=1)

            final_score = torch.mean(votes, dim=1, keepdim=True)

        return {
            'ensemble_score': final_score,
            'lstm_score': lstm_anomaly_score,
            'transformer_score': transformer_score,
            'cnn_score': cnn_anomaly_score,
            'lstm_reconstruction': lstm_reconstruction,
            'transformer_reconstruction': transformer_reconstruction
        }


class DeepLearningDetector(BaseDetector):
    """
    🧠 Advanced Deep Learning Anomaly Detection System
    
    State-of-the-art neural network ensemble for financial anomaly detection
    inspired by advanced genomic analysis techniques. Combines LSTM, Transformer,
    and CNN architectures for comprehensive pattern recognition.
    
    Biological Analogy:
    - LSTM → Sequential DNA analysis
    - Transformer → Global genetic interaction mapping
    - CNN → Local motif detection
    - Ensemble → Multi-technique validation
    """

    def __init__(self,
                 name: str = "DeepLearningDetector",
                 config: Optional[DeepLearningConfig] = None):
        """
        Initialize deep learning detection system.
        
        Args:
            name: Detector identifier
            config: Deep learning configuration
        """
        super().__init__(name, threshold=0.95)

        self.config = config or DeepLearningConfig()

        # Model components
        self.model: Optional[EnsembleAnomalyDetector] = None
        self.scaler: Optional[StandardScaler] = None
        self.is_trained = False

        # Training data storage
        self._training_data = []
        self._training_losses = []

        # Device configuration
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        logger.info(f"Initialized {self.name} with ensemble architecture")
        logger.info(f"Using device: {self.device}")

    def _prepare_features(self, data: np.ndarray) -> np.ndarray:
        """
        🔧 Advanced feature engineering for financial time series
        
        Creates comprehensive feature set including technical indicators,
        statistical measures, and market microstructure features.
        
        Args:
            data: Raw financial data [samples, features]
            
        Returns:
            Enhanced feature matrix
        """
        if data.shape[1] < 4:  # Expect OHLC at minimum
            logger.warning("Insufficient features for advanced feature engineering")
            return data

        df = pd.DataFrame(data, columns=['open', 'high', 'low', 'close'] +
                         [f'feature_{i}' for i in range(4, data.shape[1])])

        features = []

        # Original OHLC
        features.extend([df['open'], df['high'], df['low'], df['close']])

        # Returns
        features.append(df['close'].pct_change().fillna(0))
        features.append(df['close'].pct_change(5).fillna(0))  # 5-day return

        # Technical indicators if enabled
        if self.config.use_technical_indicators:
            # Moving averages
            features.append(df['close'].rolling(10).mean().fillna(method='bfill'))
            features.append(df['close'].rolling(20).mean().fillna(method='bfill'))
            features.append(df['close'].rolling(50).mean().fillna(method='bfill'))

            # Volatility
            features.append(df['close'].rolling(20).std().fillna(method='bfill'))

            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            features.append(rsi.fillna(50))

            # MACD
            ema12 = df['close'].ewm(span=12).mean()
            ema26 = df['close'].ewm(span=26).mean()
            macd = ema12 - ema26
            signal = macd.ewm(span=9).mean()
            features.extend([macd.fillna(0), signal.fillna(0)])

            # Bollinger Bands
            bb_middle = df['close'].rolling(20).mean()
            bb_std = df['close'].rolling(20).std()
            bb_upper = bb_middle + (bb_std * 2)
            bb_lower = bb_middle - (bb_std * 2)
            bb_position = (df['close'] - bb_lower) / (bb_upper - bb_lower)
            features.append(bb_position.fillna(0.5))

        # Volume features if available and enabled
        if self.config.include_volume_features and data.shape[1] > 4:
            volume = df.iloc[:, 4] if data.shape[1] > 4 else None
            if volume is not None:
                features.append(volume)
                features.append(volume.rolling(10).mean().fillna(method='bfill'))
                # Volume-price trend
                vpt = volume * df['close'].pct_change()
                features.append(vpt.fillna(0))

        # Combine all features
        feature_matrix = np.column_stack([f.values for f in features])

        # Handle any remaining NaN values
        feature_matrix = np.nan_to_num(feature_matrix, nan=0.0, posinf=0.0, neginf=0.0)

        return feature_matrix

    def _create_sequences(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        📊 Create sequences for time series modeling
        
        Args:
            data: Feature matrix [samples, features]
            
        Returns:
            Tuple of (sequences, targets) for training
        """
        sequences = []
        targets = []

        seq_len = self.config.sequence_length

        for i in range(seq_len, len(data)):
            sequence = data[i-seq_len:i]
            target = data[i]  # Next time step

            sequences.append(sequence)
            targets.append(target)

        return np.array(sequences), np.array(targets)

    def fit(self, training_data: np.ndarray) -> Dict[str, Any]:
        """
        🎓 Train the deep learning ensemble
        
        Args:
            training_data: Historical financial data for training
            
        Returns:
            Training results and metrics
        """
        logger.info(f"Training deep learning detector with {len(training_data)} samples")

        try:
            # Feature engineering
            features = self._prepare_features(training_data)

            # Normalize features
            if self.config.normalize_features:
                self.scaler = StandardScaler()
                features_scaled = self.scaler.fit_transform(features)
            else:
                features_scaled = features
                self.scaler = None

            # Create sequences
            sequences, targets = self._create_sequences(features_scaled)

            if len(sequences) < 100:
                raise ValueError("Insufficient data for training (need at least 100 sequences)")

            # Train/validation split
            train_sequences, val_sequences, train_targets, val_targets = train_test_split(
                sequences, targets, test_size=0.2, random_state=42
            )

            # Convert to PyTorch tensors
            train_sequences = torch.FloatTensor(train_sequences).to(self.device)
            val_sequences = torch.FloatTensor(val_sequences).to(self.device)
            train_targets = torch.FloatTensor(train_targets).to(self.device)
            val_targets = torch.FloatTensor(val_targets).to(self.device)

            # Create data loaders
            train_dataset = TensorDataset(train_sequences, train_targets)
            val_dataset = TensorDataset(val_sequences, val_targets)

            train_loader = DataLoader(train_dataset, batch_size=self.config.batch_size, shuffle=True)
            val_loader = DataLoader(val_dataset, batch_size=self.config.batch_size, shuffle=False)

            # Initialize model
            input_size = features_scaled.shape[1]
            self.model = EnsembleAnomalyDetector(input_size, self.config).to(self.device)

            # Optimizer and loss
            optimizer = optim.Adam(self.model.parameters(), lr=self.config.learning_rate)
            scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)

            # Training loop
            best_val_loss = float('inf')
            patience_counter = 0
            training_losses = []
            validation_losses = []

            for epoch in range(self.config.num_epochs):
                # Training phase
                self.model.train()
                train_loss = 0.0

                for batch_sequences, batch_targets in train_loader:
                    optimizer.zero_grad()

                    outputs = self.model(batch_sequences)

                    # Combined loss: reconstruction + anomaly detection
                    reconstruction_loss = F.mse_loss(outputs['lstm_reconstruction'], batch_sequences)
                    transformer_loss = F.mse_loss(outputs['transformer_reconstruction'], batch_sequences)

                    # For training, use normal data (low anomaly scores)
                    normal_target = torch.zeros_like(outputs['ensemble_score'])
                    anomaly_loss = F.binary_cross_entropy(outputs['ensemble_score'], normal_target)

                    total_loss = reconstruction_loss + transformer_loss + anomaly_loss
                    total_loss.backward()

                    # Gradient clipping
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)

                    optimizer.step()
                    train_loss += total_loss.item()

                # Validation phase
                self.model.eval()
                val_loss = 0.0

                with torch.no_grad():
                    for batch_sequences, batch_targets in val_loader:
                        outputs = self.model(batch_sequences)

                        reconstruction_loss = F.mse_loss(outputs['lstm_reconstruction'], batch_sequences)
                        transformer_loss = F.mse_loss(outputs['transformer_reconstruction'], batch_sequences)
                        normal_target = torch.zeros_like(outputs['ensemble_score'])
                        anomaly_loss = F.binary_cross_entropy(outputs['ensemble_score'], normal_target)

                        total_loss = reconstruction_loss + transformer_loss + anomaly_loss
                        val_loss += total_loss.item()

                # Calculate average losses
                avg_train_loss = train_loss / len(train_loader)
                avg_val_loss = val_loss / len(val_loader)

                training_losses.append(avg_train_loss)
                validation_losses.append(avg_val_loss)

                # Learning rate scheduling
                scheduler.step(avg_val_loss)

                # Early stopping
                if avg_val_loss < best_val_loss:
                    best_val_loss = avg_val_loss
                    patience_counter = 0
                    # Save best model
                    self.best_model_state = self.model.state_dict().copy()
                else:
                    patience_counter += 1

                if epoch % 10 == 0:
                    logger.debug(f"Epoch {epoch}: Train Loss={avg_train_loss:.6f}, Val Loss={avg_val_loss:.6f}")

                if patience_counter >= self.config.early_stopping_patience:
                    logger.info(f"Early stopping at epoch {epoch}")
                    break

            # Load best model
            if hasattr(self, 'best_model_state'):
                self.model.load_state_dict(self.best_model_state)

            # Calculate anomaly threshold using validation data
            self.model.eval()
            anomaly_scores = []

            with torch.no_grad():
                for batch_sequences, _ in val_loader:
                    outputs = self.model(batch_sequences)
                    scores = outputs['ensemble_score'].cpu().numpy()
                    anomaly_scores.extend(scores.flatten())

            # Set threshold at specified percentile
            self.threshold = np.percentile(anomaly_scores, self.config.anomaly_threshold * 100)

            self.is_trained = True
            self._training_losses = training_losses

            training_results = {
                'training_completed': True,
                'epochs_trained': epoch + 1,
                'best_validation_loss': best_val_loss,
                'anomaly_threshold': self.threshold,
                'training_samples': len(train_sequences),
                'validation_samples': len(val_sequences),
                'feature_dimension': input_size,
                'model_parameters': sum(p.numel() for p in self.model.parameters()),
                'device_used': str(self.device)
            }

            logger.info(f"Training completed: {training_results}")

            return training_results

        except Exception as e:
            logger.error(f"Training failed: {str(e)}")
            raise

    def detect_anomalies(self,
                        model_genome: FinancialGenome,
                        data: np.ndarray) -> DetectionResult:
        """
        🔍 Detect anomalies using deep learning ensemble
        
        Args:
            model_genome: Financial model genome
            data: Recent financial data
            
        Returns:
            Comprehensive detection results
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before detection")

        logger.debug(f"Detecting anomalies in {len(data)} samples")

        try:
            # Feature engineering
            features = self._prepare_features(data)

            # Normalize if scaler was fitted
            if self.scaler is not None:
                features_scaled = self.scaler.transform(features)
            else:
                features_scaled = features

            # Create sequences for the most recent period
            if len(features_scaled) < self.config.sequence_length:
                # Pad with zeros if insufficient data
                padding = np.zeros((self.config.sequence_length - len(features_scaled), features_scaled.shape[1]))
                features_scaled = np.vstack([padding, features_scaled])

            # Get the most recent sequence
            recent_sequence = features_scaled[-self.config.sequence_length:]

            # Convert to tensor
            sequence_tensor = torch.FloatTensor(recent_sequence).unsqueeze(0).to(self.device)

            # Perform detection
            self.model.eval()
            with torch.no_grad():
                outputs = self.model(sequence_tensor)

                ensemble_score = outputs['ensemble_score'].cpu().numpy()[0, 0]
                lstm_score = outputs['lstm_score'].cpu().numpy()[0, 0]
                transformer_score = outputs['transformer_score'].cpu().numpy()[0, 0]
                cnn_score = outputs['cnn_score'].cpu().numpy()[0, 0]

            # Determine if anomaly
            anomaly_detected = ensemble_score > self.threshold

            # Calculate confidence
            confidence = min(1.0, max(0.0, (ensemble_score - 0.5) * 2))

            # Identify affected regions (simplified)
            affected_regions = []
            if anomaly_detected:
                if lstm_score > 0.5:
                    affected_regions.append("temporal_patterns")
                if transformer_score > 0.5:
                    affected_regions.append("attention_patterns")
                if cnn_score > 0.5:
                    affected_regions.append("local_features")

            detection_result = DetectionResult(
                anomaly_detected=anomaly_detected,
                anomaly_score=float(ensemble_score),
                affected_regions=affected_regions,
                confidence=confidence,
                timestamp=datetime.now(),
                metadata={
                    'detector_type': 'deep_learning_ensemble',
                    'lstm_score': float(lstm_score),
                    'transformer_score': float(transformer_score),
                    'cnn_score': float(cnn_score),
                    'threshold_used': self.threshold,
                    'sequence_length': self.config.sequence_length,
                    'feature_dimension': features_scaled.shape[1]
                }
            )

            logger.debug(f"Detection complete: anomaly={anomaly_detected}, score={ensemble_score:.3f}")

            return detection_result

        except Exception as e:
            logger.error(f"Anomaly detection failed: {str(e)}")
            raise

    def get_feature_importance(self) -> Dict[str, float]:
        """
        📊 Calculate feature importance using gradient-based methods
        
        Returns:
            Dictionary of feature importance scores
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before calculating feature importance")

        # This is a simplified feature importance calculation
        # In practice, you might use more sophisticated methods like SHAP

        feature_names = [
            'open', 'high', 'low', 'close', 'return_1d', 'return_5d',
            'ma_10', 'ma_20', 'ma_50', 'volatility', 'rsi', 'macd', 'signal',
            'bb_position'
        ]

        # For now, return uniform importance
        # This could be enhanced with actual gradient-based importance
        importance = {name: 1.0 / len(feature_names) for name in feature_names}

        return importance

    def save_model(self, filepath: str):
        """💾 Save trained model to disk"""
        if not self.is_trained:
            raise ValueError("No trained model to save")

        save_dict = {
            'model_state_dict': self.model.state_dict(),
            'config': self.config.__dict__,
            'scaler': self.scaler,
            'threshold': self.threshold,
            'training_losses': self._training_losses
        }

        torch.save(save_dict, filepath)
        logger.info(f"Model saved to {filepath}")

    def load_model(self, filepath: str):
        """📂 Load trained model from disk"""
        save_dict = torch.load(filepath, map_location=self.device)

        # Recreate config
        config_dict = save_dict['config']
        self.config = DeepLearningConfig(**config_dict)

        # Determine input size from saved scaler or use default
        if save_dict['scaler'] is not None:
            input_size = save_dict['scaler'].n_features_in_
        else:
            input_size = 14  # Default feature count

        # Recreate model
        self.model = EnsembleAnomalyDetector(input_size, self.config).to(self.device)
        self.model.load_state_dict(save_dict['model_state_dict'])

        # Restore other attributes
        self.scaler = save_dict['scaler']
        self.threshold = save_dict['threshold']
        self._training_losses = save_dict.get('training_losses', [])
        self.is_trained = True

        logger.info(f"Model loaded from {filepath}")
