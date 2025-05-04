import {
  Button,
  ButtonGroup,
  DialogActionTrigger,
  Input,
  Text,
  VStack,
} from "@chakra-ui/react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { type SubmitHandler, useForm } from "react-hook-form";
import { FaExchangeAlt } from "react-icons/fa";

import {
  type ApiError,
  type PersonaPublic,
  PersonasService,
} from "../../client";
import useCustomToast from "@/hooks/useCustomToast";
import { handleError } from "@/utils";
import {
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogRoot,
  DialogTitle,
  DialogTrigger,
} from "../ui/dialog";
import { Field } from "../ui/field";

interface EditPersonaProps {
  persona: PersonaPublic;
}

interface PersonaUpdateForm {
  name: string;
  description?: string | null;
  long_description?: string | null;
  general_domain?: string | null;
  specific_domain?: string | null;
  general_domain_high?: string | null;
  specific_domain_high?: string | null;
}

const EditPersona = ({ persona }: EditPersonaProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const queryClient = useQueryClient();
  const { showSuccessToast } = useCustomToast();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<PersonaUpdateForm>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      ...persona,
      description: persona.description ?? undefined,
    },
  });

  const mutation = useMutation({
    mutationFn: (data: PersonaUpdateForm) =>
      PersonasService.updatePersona({
        id: persona.id,
        requestBody: data,
      }),
    onSuccess: () => {
      showSuccessToast("Persona updated successfully.");
      reset();
      setIsOpen(false);
    },
    onError: (err: ApiError) => {
      handleError(err);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["personas"] });
    },
  });

  const onSubmit: SubmitHandler<PersonaUpdateForm> = async (data) => {
    mutation.mutate(data);
  };

  return (
    <DialogRoot
      size={{ base: "xs", md: "md" }}
      placement="center"
      open={isOpen}
      onOpenChange={({ open }) => setIsOpen(open)}
    >
      <DialogTrigger asChild>
        <Button variant="ghost">
          <FaExchangeAlt fontSize="16px" />
          Edit Persona
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Edit Persona</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text mb={4}>Update the persona details below.</Text>
            <VStack gap={4}>
              <Field
                required
                invalid={!!errors.name}
                errorText={errors.name?.message}
                label="Name"
              >
                <Input
                  id="name"
                  {...register("name", {
                    required: "Name is required",
                  })}
                  placeholder="Name"
                  type="text"
                />
              </Field>

              <Field
                invalid={!!errors.description}
                errorText={errors.description?.message}
                label="Description"
              >
                <Input
                  id="description"
                  {...register("description")}
                  placeholder="Description"
                  type="text"
                />
              </Field>
              <Field
                invalid={!!errors.long_description}
                errorText={errors.long_description?.message}
                label="Long Description"
              >
                <Input
                  id="long_description"
                  {...register("long_description")}
                  placeholder="Long Description"
                  type="text"
                />
              </Field>
              <Field
                invalid={!!errors.general_domain}
                errorText={errors.general_domain?.message}
                label="General Domain"
              >
                <Input
                  id="general_domain"
                  {...register("general_domain")}
                  placeholder="General Domain"
                  type="text"
                />
              </Field>
              <Field
                invalid={!!errors.specific_domain}
                errorText={errors.specific_domain?.message}
                label="Specific Domain"
              >
                <Input
                  id="specific_domain"
                  {...register("specific_domain")}
                  placeholder="Specific Domain"
                  type="text"
                />
              </Field>
              <Field
                invalid={!!errors.general_domain_high}
                errorText={errors.general_domain_high?.message}
                label="General Domain High"
              >
                <Input
                  id="general_domain_high"
                  {...register("general_domain_high")}
                  placeholder="General Domain High"
                  type="text"
                />
              </Field>
              <Field
                invalid={!!errors.specific_domain_high}
                errorText={errors.specific_domain_high?.message}
                label="Specific Domain High"
              >
                <Input
                  id="specific_domain_high"
                  {...register("specific_domain_high")}
                  placeholder="Specific Domain High"
                  type="text"
                />
              </Field>
            </VStack>
          </DialogBody>

          <DialogFooter gap={2}>
            <ButtonGroup>
              <DialogActionTrigger asChild>
                <Button
                  variant="subtle"
                  colorPalette="gray"
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
              </DialogActionTrigger>
              <Button variant="solid" type="submit" loading={isSubmitting}>
                Save
              </Button>
            </ButtonGroup>
          </DialogFooter>
        </form>
        <DialogCloseTrigger />
      </DialogContent>
    </DialogRoot>
  );
};

export default EditPersona;
