import lightning.pytorch as pl
import torch.nn.functional as Functional
import torch
from geom3d.models import SchNet, DimeNet, DimeNetPlusPlus, GemNet, SphereNet


class Pymodel(pl.LightningModule):
    def __init__(self, model, graph_pred_linear):
        super().__init__()
        self.save_hyperparameters(ignore=["graph_pred_linear", "model"])
        self.molecule_3D_repr = model
        self.graph_pred_linear = graph_pred_linear

    def training_step(self, batch, batch_idx):
        # training_step defines the train loop.
        loss = self._get_preds_loss_accuracy(batch)

        self.log("train_loss", loss, batch_size=batch.size(0))
        return loss

    def validation_step(self, batch, batch_idx):
        """used for logging metrics"""
        loss = self._get_preds_loss_accuracy(batch)

        # Log loss and metric
        self.log("val_loss", loss, batch_size=batch.size(0))
        return loss

    def _get_preds_loss_accuracy(self, batch):
        """convenience function since train/valid/test steps are similar"""
        if self.graph_pred_linear is not None:
            z = self.molecule_3D_repr(batch.x, batch.positions, batch.batch)
            z = self.graph_pred_linear(z)
            loss = Functional.mse_loss(z, batch.y.unsqueeze(1))

        else:
            z = self.molecule_3D_repr(
                batch.x, batch.positions, batch.batch
            ).squeeze()
            loss = Functional.mse_loss(z, batch.y)

        return loss

    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=5e-4)
        return optimizer

    def forward(self, batch):
        z = self.molecule_3D_repr(batch.x, batch.positions, batch.batch)
        z = self.graph_pred_linear(z)
        return z


def model_setup(config):
    model_config = config["model"]
    if config["model_name"] == "SchNet":
        model = SchNet(
            hidden_channels=model_config["emb_dim"],
            num_filters=model_config["SchNet_num_filters"],
            num_interactions=model_config["SchNet_num_interactions"],
            num_gaussians=model_config["SchNet_num_gaussians"],
            cutoff=model_config["SchNet_cutoff"],
            readout=model_config["SchNet_readout"],
            node_class=model_config["node_class"],
        )
        graph_pred_linear = torch.nn.Linear(
            model_config["emb_dim"], model_config["num_tasks"]
        )

    elif config["model_name"] == "DimeNet":
        model = DimeNet(
            node_class=model_config["node_class"],
            hidden_channels=model_config["hidden_channels"],
            out_channels=model_config["out_channels"],
            num_blocks=model_config["num_blocks"],
            num_bilinear=model_config["num_bilinear"],
            num_spherical=model_config["num_spherical"],
            num_radial=model_config["num_radial"],
            cutoff=model_config["cutoff"],
            envelope_exponent=model_config["envelope_exponent"],
            num_before_skip=model_config["num_before_skip"],
            num_after_skip=model_config["num_after_skip"],
            num_output_layers=model_config["num_output_layers"],
        )
        graph_pred_linear = None

    elif config["model_name"] == "DimeNetPlusPlus":
        model = DimeNetPlusPlus(
            node_class=model_config["node_class"],
            hidden_channels=model_config["hidden_channels"],
            out_channels=model_config["out_channels"],
            num_blocks=model_config["num_blocks"],
            int_emb_size=model_config["int_emb_size"],
            basis_emb_size=model_config["basis_emb_size"],
            out_emb_channels=model_config["out_emb_channels"],
            num_spherical=model_config["num_spherical"],
            num_radial=model_config["num_radial"],
            cutoff=model_config["cutoff"],
            envelope_exponent=model_config["envelope_exponent"],
            num_before_skip=model_config["num_before_skip"],
            num_after_skip=model_config["num_after_skip"],
            num_output_layers=model_config["num_output_layers"],
        )
        graph_pred_linear = None

    elif config["model_name"] == "GemNet":
        model = GemNet(
            node_class=model_config["node_class"],
            num_targets=model_config["num_targets"],
            num_blocks=model_config["num_blocks"],
            emb_size_atom=model_config["emb_size_atom"],
            emb_size_edge=model_config["emb_size_edge"],
            emb_size_trip=model_config["emb_size_trip"],
            emb_size_quad=model_config["emb_size_quad"],
            emb_size_rbf=model_config["emb_size_rbf"],
            emb_size_cbf=model_config["emb_size_cbf"],
            emb_size_sbf=model_config["emb_size_sbf"],
            emb_size_bil_quad=model_config["emb_size_bil_quad"],
            emb_size_bil_trip=model_config["emb_size_bil_trip"],
            num_concat=model_config["num_concat"],
            num_atom=model_config["num_atom"],
            triplets_only=model_config["triplets_only"],
            direct_forces=model_config["direct_forces"],
            extensive=model_config["extensive"],
            forces_coupled=model_config["forces_coupled"],
            cutoff=model_config["cutoff"],
            int_cutoff=model_config["int_cutoff"],
            envelope_exponent=model_config["envelope_exponent"],
            num_spherical=model_config["num_spherical"],
            num_radial=model_config["num_radial"],
            num_before_skip=model_config["num_before_skip"],
            num_after_skip=model_config["num_after_skip"],
        )
        graph_pred_linear = None

    elif config["model_name"] == "SphereNet":
        model = SphereNet(
            energy_and_force=False,
            hidden_channels=model_config["hidden_channels"],
            out_channels=model_config["out_channels"],
            cutoff=model_config["cutoff"],
            num_layers=model_config["num_layers"],
            int_emb_size=model_config["int_emb_size"],
            basis_emb_size_dist=model_config["basis_emb_size_dist"],
            basis_emb_size_angle=model_config["basis_emb_size_angle"],
            basis_emb_size_torsion=model_config["basis_emb_size_torsion"],
            out_emb_channels=model_config["out_emb_channels"],
            num_spherical=model_config["num_spherical"],
            num_radial=model_config["num_radial"],
            envelope_exponent=model_config["envelope_exponent"],
            num_before_skip=model_config["num_before_skip"],
            num_after_skip=model_config["num_after_skip"],
            num_output_layers=model_config["num_output_layers"],
        )
        graph_pred_linear = None
    else:
        raise ValueError("Invalid model name")
    
    return model, graph_pred_linear